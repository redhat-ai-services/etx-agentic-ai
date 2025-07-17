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
    "http://llamastack-with-config-service.default.svc.cluster.local:8321"
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
    user_prompts = [
        f"Review the OpenShift logs for the pod '{pod_name}',in the '{namespace}' namespace. "
        "If the logs indicate an error search for the solution, " 
        "create a summary message with the category and explanation of the error, "
        'create a Github issue using {"name":"create_issue","arguments":'
        '{"owner":"redhat-ai-services","repo":"etx-agentic-ai",'
        '"title":"Issue with Etx pipeline","body":"summary of the error"}}}. DO NOT add any optional parameters.'
    ]
    session_id = agent.create_session("agent-session")
    for prompt in user_prompts:
        print("\n"+"="*50)
        print(f"Processing user query: {prompt}")
        print("="*50)
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
        step_printer(response.steps)