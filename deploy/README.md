# Solomon on the DeepThink VM

Peter and Desrosier are the only Adults. The app does not ask anyone to sign in. The Linux account `solomon` is the service account that runs Solomon and Hermes. It is not a Member.

One Ubuntu 24.04 VM on DeepThink, named `solomon`, beside the Home Assistant VM and the UniFi OS VM. Solomon (the FastAPI app and the built web UI) and Hermes run on that VM as `solomon` and come back after a reboot through systemd.

The app starts the way the repo already starts it: `python -m solomon`, which runs uvicorn on `create_app` and serves `web/dist` on port 8000. This install does not add a container, Docker Compose, or a Docker socket. ADR-0002 describes an image this repo does not have.

SQLite and receipt blobs live in `/var/lib/solomon`. An update pulls `main`, reinstalls, rebuilds the web UI, and restarts the service. It does not delete that directory.

## What to create

- Ubuntu 24.04
- 2 vCPU
- 2 GB RAM, pinned, no balloon. If the Hermes installer runs out of memory, raise this VM to 4 GB. Leave Home Assistant's memory alone, and do not create another VM.
- 32 GB disk
- A fixed address on the home LAN
- SSH from inside the house

## Leave these off

- No Ollama VM. That waits until the house wants a model that stays on the LAN.
- No port forward on the Verizon router. Leave UPnP off. Nothing on the public internet should reach this VM.
- No Cloudflare Tunnel. Do not install `cloudflared`.
- No email gateway, Discord, or AgentMail.
- Do not run `hermes setup --portal`. That command also turns on Nous web search, image generation, text-to-speech, and a cloud browser.
- Do not copy `~/.hermes/auth.json`, a refresh token, or an API key into the repo, the docs, chat, or Slack.

## Install

On the new VM, as an administrator:

```bash
sudo apt-get update
sudo apt-get install -y git
sudo git clone https://github.com/desrosiertech/solomon-hub.git /opt/solomon/app
sudo bash /opt/solomon/app/deploy/install.sh
```

The script is safe to run again. A later run fetches `main`, installs the Python package, runs `npm ci` and `npm run build`, and restarts `solomon.service`. Hermes is installed once, with the official installer:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-browser --skip-computer-use --non-interactive
```

`--non-interactive` keeps the installer from opening the setup wizard. The script then sets Hermes with `hermes config set`, so a second run changes the existing keys instead of duplicating them:

```yaml
model:
  provider: nous
  default: anthropic/claude-opus-4.6
  base_url: https://inference-api.nousresearch.com/v1

skills:
  write_approval: true

agent:
  disabled_toolsets:
    - terminal
    - web
    - browser
    - image_gen
    - video_gen
    - code_execution
    - computer_use
    - file
    - cronjob
    - delegation
```

Memory stays on. Skills stay on. `write_approval: true` means a skill that can act waits for an Adult.

The script installs the Hermes gateway as a user service and enables lingering, so Hermes is supervised across reboot. It does not attach Discord, email, or AgentMail. Leave `hermes gateway setup` unused.

The script installs Tailscale and stops. Join the tailnet yourself. Do not pass an auth key:

```bash
sudo tailscale up
```

Approve the machine in the Tailscale admin page. Leave Funnel off. Phones open `http://<tailscale-name>:8000`. On the home LAN, open `http://<fixed-lan-address>:8000`.

The service listens on port 8000 on the VM (`SOLOMON_HOST=0.0.0.0`). The Verizon router still has no forward, so that port is the LAN address and the tailnet address.

## Nous login

Stop unless the person who created the Nous account is at the keyboard. They sign in with a browser on their own computer. Peter does not type their password.

As `solomon`:

```bash
hermes auth add nous --type oauth
```

Hermes prints a code or a URL. The account owner opens it on their own computer and approves it. If the page cannot reach the VM, use the official remote steps: https://hermes-agent.nousresearch.com/docs/guides/run-hermes-with-nous-portal

Then:

```bash
chmod 600 ~/.hermes/auth.json
sudo systemctl restart solomon
```

The restart matters. Solomon reads the login file when the process starts. Until this restart, the reader stays off and Chat keeps the message.

Official install notes: https://hermes-agent.nousresearch.com/docs/getting-started/installation

If `hermes` is not found, open a new shell. The launcher is `~/.local/bin/hermes`.

## Check

```bash
hermes portal info
hermes doctor
hermes config get model.default
systemctl is-active solomon
systemctl is-enabled solomon
hermes gateway status
```

Pass looks like this:

- `http://<fixed-lan-address>:8000` shows the dashboard.
- Auth says logged in.
- Model says Nous is the inference provider.
- `model.default` is `anthropic/claude-opus-4.6`.
- Web search, image generation, browser, and cloud terminal are not routed through Nous. If `hermes portal info` says they are, the toolsets did not stick. Fix that before calling this done.
- `hermes doctor` reports no storage error.
- `solomon.service` is active and enabled.
- `~/.hermes/auth.json` is mode 600.
- `/var/lib/solomon/solomon.db` exists and is owned by `solomon`.
- A phone on cellular data, off the tailnet, cannot open the VM, SSH, or port 8000.

Do not test Hermes by asking it to search the web. That toolset is off on purpose.

From a phone on cellular data, the house's public address should not answer for Solomon. If a forward exists, remove it before putting household records on the VM.

## Update

On the VM:

```bash
sudo bash /opt/solomon/app/deploy/install.sh
```

That is the update. It leaves `/var/lib/solomon` in place.

## Done when

- One new VM exists beside Home Assistant and UniFi OS.
- Solomon answers on the LAN address and, after Tailscale is joined, on the tailnet address.
- Both services come back after a reboot.
- Hermes is installed as `solomon`.
- The Nous account owner has finished the browser login, and Solomon has been restarted after that.
- The model is `anthropic/claude-opus-4.6` through Nous.
- Terminal, web, browser, image generation, video generation, code execution, computer use, file, cron, and delegation are off.
- The login file is mode 600 and is not in the repo.
- No new port is open on the Verizon router.
