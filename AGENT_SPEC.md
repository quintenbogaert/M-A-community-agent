# Agent Specification

## Purpose

Build an AI agent capable of carrying out multi-step research and operational tasks.

## Initial input

A task supplied by the user.

## Initial capabilities

- communicate with an LLM
- produce structured output

## Future capabilities

- search external information
- read approved files
- write results to approved folders
- maintain task state
- plan multi-step tasks
- verify results
- autonomously execute tasks
- connect to approved external accounts and services
- read data from approved services such as Slack
- perform approved actions in connected services, such as sending a Slack message
- use APIs and integrations where explicitly authorized
- Any features added later on should be added in the README file

## External accounts and services

The agent may eventually connect to user-authorized services such as:

- Slack
- email
- calendars
- cloud storage
- databases
- business software
- other API-enabled services

Each connected service must be treated as a separate permission boundary.

The agent should only receive the minimum access required for the task.

Where possible, access should be scoped by:

- account
- workspace
- channel
- folder
- resource
- action type
- read versus write permission

For example: 
Laptop permissions:
- /workspace/input → read
- /workspace/output → write
- everything else → no access

Slack permissions:
- #ma-research → read
- #deal-team → read/write
- direct messages → no access
- workspace administration → no access

The agent must not automatically receive full access to an account merely because an integration exists.

Sensitive actions, such as sending messages, deleting data, changing permissions, or making irreversible changes, may require explicit user approval.

Authentication credentials, API keys, OAuth tokens, and other secrets must not be hard-coded into the source code or Docker image.

## Security

The agent must follow the principle of least privilege.

It should only be able to access tools, files, directories, network resources, accounts, and external services that have explicitly been made available to it.

Eventually, the agent will run inside Docker so that access to the host computer can be controlled.

External service access should also be controlled independently from Docker permissions.

## Autonomy

Increasing autonomy should not automatically imply increasing permissions.

The agent may become highly autonomous in how it completes a task while still operating within strict limits on:

- filesystem access
- network access
- connected accounts
- available tools
- permitted actions
- spending
- execution time

## Auditability

The agent should maintain an audit trail of important actions, including:

- tools used
- files accessed
- services contacted
- API calls made
- messages sent
- data written or modified
- approvals requested
- errors encountered