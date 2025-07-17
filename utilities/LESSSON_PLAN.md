=== LESSON PLAN

pre-reqs

1. Teams of 2 people per cluster. 
2. Login details.
3. Fork Git Code.

whats in the cluster
- Juliano's etx-ai cluster (RHOAI, GPU, NFD)
- bootstrap 
    - ACM + ArgoCD
        - vault
        - observability
        - LLM granite is there maas (with no tool calling config in vllm at start - so it breaks)
        - pipeline add exists in failing state
        - Containerfile + BuildConfig/Tekton Pipeline for as a Service (disabled)
        - workbench creation + rbac
- apps
    - Vault setup
    - api tokens:
        tavily token
        git token
        maas
    - workbench describe bootstrap
    - use case
        - challenge, definition, steps / approach
        - explain about tool + agents
    - app deploy flow:
        - 🦙 LLamaStack - LLD + ConfigMap
            - 0. llama-stack-client - list providers, list models
            - 1. add in direct granite model, chat completion
            - 2. builtin::websearch - test simple - 🐛 first break (not tool call vllm model); fix it
            - 3. maas - because of fails
            - 4. mcp::openshift - simple vs react; fail with simple
            - 5. mcp::github - react
        - Playground (run serially)
            - 1. prompt chat model
            - 2. query the weather for today; discuss tool; copy-paste search for solution to error logs; introduce simple agent builtin::websearch
            - 3. chat to new models, simple tools call, comparison of failed simple vs working maas
            - 4. simple vs react, query namespace pod for a pod error; copy-paste search for solution to error logs
            - 5. create issue, add issue comments
            - 6. prompt engineering; create the final prompt 🍺
        - Notebook (one notebook)
            - 1. simple prompts the model/llama-stack - chat completion
            - 2. query builtin::websearch; tool calling; custom function call
            - 3. mcp::openshift
            - 4. prompt chaining; react
            - 5. mcp::github
            - 6. we have an agent; max token parameters + search strategy - changing these;
            - 7. prototype service; endpoint; flask app; trigger it in nootebook/terminal
        - Deploy as a Service
            - 1. Agent lifecycle / SDLC / Tekton pipeline (builds + deploys agent)
            - 2. Configure trigger from failing app -> Agent; rerun app pipeline
            - MVP Done ✅
        - Observability + Evals (back to Notebooks)
            - 1. run evals notebook
            - 2. observe 👀; loook for evals; rerun pipeline; look for agent interactions; tempo dashboard;
        - Stretch Assignment:
            - Add RAG to agent to pull from docs (identify a type of issue you wish to solve, find the relevant docs, embed, query)
            - Create and deploy agent
            - Create evals for the new agent
