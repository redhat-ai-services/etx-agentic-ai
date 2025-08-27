from os import environ
from pprint import pprint

from llama_stack_client import Agent, LlamaStackClient
from llama_stack_client.lib.agents.react.agent import ReActAgent
from llama_stack_client.lib.agents.react.tool_parser import ReActOutput
from llama_stack_client.lib.agents.event_logger import EventLogger
from termcolor import cprint

from utils import step_printer


llama_stack_url = environ.get(
    'LLAMA_STACK_URL',
    "http://llamastack-with-config-service.llama-stack.svc.cluster.local:8321"
)
model_id = environ.get('MODEL_ID', "granite-31-2b-instruct")
model_prompt = """
You are a helpful assistant. You have access to a number of tools.
Whenever a tool is called, be sure to return the Response in a friendly and helpful tone.
"""
temperature = float(environ.get('TEMPERATURE', '0.0'))
strategy = {"type": "greedy"}
max_tokens = int(environ.get('MAX_TOKENS', '512'))
client_timeout = float(environ.get('CLIENT_TIMEOUT', '600.0'))
max_infer_iterations = int(environ.get('MAX_INFER_ITERATIONS', '10'))

print(
    f'Inference Parameters:\n\tModel: {model_id}\n'
    f'Llama Stack URL: {llama_stack_url}\n'
    f'Client timeout: {client_timeout}\n'
    f'Max infer iterations: {max_infer_iterations}\n'
    f'Temperature: {temperature}'
)


client = LlamaStackClient(
    base_url=llama_stack_url,
    timeout=client_timeout # Default is 1 min which is far too little for some agentic tests, we set it to 10 min
)
models = client.models.list()
print(f'registered models: {models}')

registered_tools = client.tools.list()
registered_toolgroups = [t.toolgroup_id for t in registered_tools]
print(f'registered toolgroups: {registered_toolgroups}')

agent = ReActAgent(
    client=client,
    model=model_id,
    tools=["mcp::openshift", "builtin::websearch", "mcp::github"],
    response_format={
        "type": "json_schema",
        "json_schema": ReActOutput.model_json_schema(),
    },
    sampling_params={"max_tokens":max_tokens},
    max_infer_iters=max_infer_iterations
)
print('instantiated ReAct agent')


def run_agent(pod_name, namespace):
    print(f'reporting failure on {pod_name} in {namespace}')
    # user_prompts = [
    #     f"Review the OpenShift logs for the pod '{pod_name}',in the '{namespace}' namespace. "
    #     "If the logs indicate an error search for the solution, " 
    #     "create a summary message with the category and explanation of the error, "
    #     'create a Github issue using {"name":"create_issue","arguments":'
    #     '{"owner":"redhat-ai-services","repo":"etx-agentic-ai",'
    #     '"title":"Issue with Etx pipeline","body":"summary of the error"}}}. DO NOT add any optional parameters.'
    # ]
    # Build prompt safely to avoid f-string formatting issues
    try:
        print(f"Building prompt for pod: {pod_name}, namespace: {namespace}")
        
        # Use .format() to avoid f-string curly brace conflicts
        prompt_template = """You are an expert OpenShift administrator. Your task is to analyze pod logs, summarize the error, and generate a JSON object to create a GitHub issue for tracking. Follow the format in the examples below.
        
        ---
        EXAMPLE 1:
        Input: The logs for pod 'frontend-v2-abcde' in namespace 'webapp' show: ImagePullBackOff: Back-off pulling image 'my-registry/frontend:latest'.

        Output:
        The pod is in an **ImagePullBackOff** state. This means Kubernetes could not pull the container image 'my-registry/frontend:latest', likely due to an incorrect image tag or authentication issues.
        {{\"name\":\"create_issue\",\"arguments\":{{\"owner\":\"redhat-ai-services\",\"repo\":\"etx-agentic-ai\",\"title\":\"Issue with Etx pipeline\",\"body\":\"### Cluster/namespace location\\nwebapp/frontend-v2-abcde\\n\\n### Summary of the problem\\nThe pod is failing to start due to an ImagePullBackOff error.\\n\\n### Detailed error/code\\nImagePullBackOff: Back-off pulling image 'my-registry/frontend:latest'\\n\\n### Possible solutions\\n1. Verify the image tag 'latest' exists in the 'my-registry/frontend' repository.\\n2. Check for authentication errors with the image registry.\"}}}}

        ---
        EXAMPLE 2:
        Input: The logs for pod 'data-processor-xyz' in namespace 'pipelines' show: CrashLoopBackOff. Last state: OOMKilled.

        Output:
        The pod is in a **CrashLoopBackOff** state because it was **OOMKilled**. The container tried to use more memory than its configured limit.
        {{\"name\":\"create_issue\",\"arguments\":{{\"owner\":\"redhat-ai-services\",\"repo\":\"etx-agentic-ai\",\"title\":\"Issue with Etx pipeline\",\"body\":\"### Cluster/namespace location\\npipelines/data-processor-xyz\\n\\n### Summary of the problem\\nThe pod is in a CrashLoopBackOff state because it was OOMKilled (Out of Memory).\\n\\n### Detailed error/code\\nCrashLoopBackOff, Last state: OOMKilled\\n\\n### Possible solutions\\n1. Increase the memory limit in the pod's deployment configuration.\\n2. Analyze the application for memory leaks.\"}}}}
        ---

        NOW, YOUR TURN:

        Input: Review the OpenShift logs for the pod '{pod_name}' in the '{namespace}' namespace. If the logs indicate an error, search for the solution, create a summary message with the category and explanation of the error, and create a Github issue using {{\"name\":\"create_issue\",\"arguments\":{{\"owner\":\"redhat-ai-services\",\"repo\":\"etx-agentic-ai\",\"title\":\"Issue with Etx pipeline\",\"body\":\"<summary of the error>\"}}}}. DO NOT add any optional parameters.

        ONLY tail the last 10 lines of the pod, no more.
        The JSON object formatted EXACTLY as outlined above.
        """
        
        # Safely format the prompt with variables
        formatted_prompt = prompt_template.format(pod_name=pod_name, namespace=namespace)
        print("✅ Prompt built successfully")
        print(f"Prompt length: {len(formatted_prompt)} characters")
        
        user_prompts = [formatted_prompt]
        
    except Exception as e:
        print(f"❌ Error building prompt: {e}")
        print(f"Error type: {type(e).__name__}")
        # Fallback to simple prompt without examples
        fallback_prompt = (
            f"Review the OpenShift logs for the pod '{pod_name}' in the '{namespace}' namespace. "
            "If the logs indicate an error, search for the solution and create a summary message. "
            "Then create a Github issue with owner 'redhat-ai-services', repo 'etx-agentic-ai', "
            "title 'Issue with Etx pipeline', and body containing the error summary."
        )
        user_prompts = [fallback_prompt]
        print("⚠️  Using fallback prompt due to formatting error")
    # Process prompts with error handling
    try:
        print("Creating agent session...")
        session_id = agent.create_session("agent-session")
        print(f"✅ Session created: {session_id}")
        
        for i, prompt in enumerate(user_prompts, 1):
            try:
                print(f"\n{'='*50}")
                print(f"Processing prompt {i}/{len(user_prompts)}")
                print(f"Prompt preview (first 200 chars): {prompt[:200]}...")
                print('='*50)
                
                print("Sending prompt to agent...")
                response = agent.create_turn(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    session_id=session_id,
                    stream=False
                )
                print("✅ Agent response received")
                step_printer(response.steps)
                
            except Exception as prompt_error:
                print(f"❌ Error processing prompt {i}: {prompt_error}")
                print(f"Error type: {type(prompt_error).__name__}")
                print("Continuing with next prompt if available...")
                continue
                
    except Exception as session_error:
        print(f"❌ Critical error in session handling: {session_error}")
        print(f"Error type: {type(session_error).__name__}")
        raise  # Re-raise critical errors
