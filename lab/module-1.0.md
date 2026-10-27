## Module 1.0: Instructions are not store knowledge (5 minutes)

No code yet. Give the assistant a role, then examine what facts it actually
has. This time includes the lab introduction.

### Sign in

1. Sign in to the virtual machine:

   **Username**: `@lab.VirtualMachine(Windows11).Username`

   **Password**: `@lab.VirtualMachine(Windows11).Password`

2. Open **Microsoft Edge** from the Windows taskbar.
3. Go to `https://ai.azure.com` and use the workshop account:

   **Username**: `@lab.CloudPortalCredential(User1).Username`

   **Access Pass**: `@lab.CloudPortalCredential(User1).AccessToken`

   >[!note]The sign-in details are also on the Resources tab.

4. If there is a **New Foundry** toggle, turn it on.
5. Select the pre-created project. Close or skip introductory dialogs.

### Open the configured deployment

Choose **Build > Models > Deployments**. Open the deployment matching
`FOUNDRY_MODEL_DEPLOYMENT` in the root `.env`, then **Open in playground**.
You need only this deployment, even if others are listed.

> A model is the underlying capability. A deployment is the named endpoint
> configured in your project. The agent adds instructions, state, and tools
> around that client.

### Give it a role

In the **Instructions** panel, paste:

```text
You are the ordering assistant for Arepa Lab, an arepa store.
```

Ask:

```text
What arepas are on your menu today, and what do they cost?
```

### Check the source, not the confidence

The reply might suggest plausible items, ask for more information, or admit
that it does not know. Whatever the wording, this conversation has no live
menu connection. A familiar item name is not proof of availability or price.

The instruction gave a role, not access to the store. In Module 1.2, tools
will provide live store data. In Module 1.3, a knowledge base will provide
documented store information.

If available, open **Continue in code** and identify the endpoint,
authentication, and deployment name. Do not copy secrets into chat.

**Checkpoint 1.** You can distinguish instructions from a source of store
facts. You have located the one deployment the agent will use.

<!-- Image refresh: use the audited Foundry home/deployment screenshots if
still accurate; replace the Sparkles playground capture before publishing. -->
