#!/usr/bin/env bash
# Repeatable install for the Solomon VM on DeepThink.
# Run on the Ubuntu guest, as an administrator:
#   sudo bash /opt/solomon/app/deploy/install.sh
# Running it again pulls main, reinstalls, rebuilds the web UI, and restarts Solomon.
# It does not delete /var/lib/solomon. It does not print or copy ~/.hermes/auth.json.
set -euo pipefail

APP_ROOT=/opt/solomon/app
VENV=/opt/solomon/venv
DATA_ROOT=/var/lib/solomon
REPO_URL=https://github.com/desrosiertech/solomon-hub.git
BRANCH=main
ACCOUNT=solomon
HOME_DIR=/home/solomon

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/install.sh" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git curl ca-certificates python3 python3-venv python3-pip nodejs npm libatomic1

if ! id -u "$ACCOUNT" >/dev/null 2>&1; then
  adduser --quiet --disabled-password --gecos "service account" --home "$HOME_DIR" "$ACCOUNT"
fi

install -d -o "$ACCOUNT" -g "$ACCOUNT" -m 0755 /opt/solomon
install -d -o "$ACCOUNT" -g "$ACCOUNT" -m 0750 "$DATA_ROOT"

update_checkout() {
  if [[ ! -d "$APP_ROOT/.git" ]]; then
    sudo -u "$ACCOUNT" -H git clone --branch "$BRANCH" "$REPO_URL" "$APP_ROOT"
  else
    chown -R "$ACCOUNT:$ACCOUNT" "$APP_ROOT"
    sudo -u "$ACCOUNT" -H git -C "$APP_ROOT" fetch origin "$BRANCH"
    sudo -u "$ACCOUNT" -H git -C "$APP_ROOT" checkout "$BRANCH"
    sudo -u "$ACCOUNT" -H git -C "$APP_ROOT" pull --ff-only origin "$BRANCH"
  fi
}

if [[ "${SOLOMON_INSTALL_REEXEC:-}" != 1 ]]; then
  update_checkout
  exec env SOLOMON_INSTALL_REEXEC=1 bash "$APP_ROOT/deploy/install.sh"
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  sudo -u "$ACCOUNT" -H python3 -m venv "$VENV"
fi
sudo -u "$ACCOUNT" -H "$VENV/bin/pip" install -e "$APP_ROOT"
sudo -u "$ACCOUNT" -H bash -c 'cd /opt/solomon/app/web && npm ci && npm run build'

install -m 0644 "$APP_ROOT/deploy/solomon.service" /etc/systemd/system/solomon.service
systemctl daemon-reload
systemctl enable solomon.service
systemctl restart solomon.service

if ! sudo -u "$ACCOUNT" -H bash -c 'command -v hermes >/dev/null 2>&1 || [[ -x "$HOME/.local/bin/hermes" ]]'; then
  sudo -u "$ACCOUNT" -H bash -lc 'curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash -s -- --skip-browser --skip-computer-use --non-interactive'
fi

solomon_exec() {
  sudo -u "$ACCOUNT" -H bash -c 'export PATH="$HOME/.local/bin:$PATH"; exec "$@"' bash "$@"
}

sudo -u "$ACCOUNT" -H python3 - <<'PY'
from pathlib import Path

path = Path.home() / ".hermes" / "config.yaml"
if not path.is_file():
    raise SystemExit(0)
lines = path.read_text(encoding="utf-8").splitlines()
out = ["model: {}" if line in ('model: ""', "model: ''") else line for line in lines]
if out != lines:
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY

solomon_exec hermes config set model.provider nous
solomon_exec hermes config set model.default anthropic/claude-opus-4.6
solomon_exec hermes config set model.base_url https://inference-api.nousresearch.com/v1
solomon_exec hermes config set skills.write_approval true
solomon_exec hermes config set agent.disabled_toolsets '["terminal", "web", "browser", "image_gen", "video_gen", "code_execution", "computer_use", "file", "cronjob", "delegation"]'

model_default="$(solomon_exec hermes config get model.default)"
case "$model_default" in
  *anthropic/claude-opus-4.6*) ;;
  *)
    echo "model.default did not stick: ${model_default}" >&2
    exit 1
    ;;
esac

base_url="$(solomon_exec hermes config get model.base_url)"
case "$base_url" in
  *https://inference-api.nousresearch.com/v1*) ;;
  *)
    echo "model.base_url did not stick: ${base_url}" >&2
    exit 1
    ;;
esac

disabled="$(solomon_exec hermes config get agent.disabled_toolsets)"
for name in terminal web browser image_gen video_gen code_execution computer_use file cronjob delegation; do
  case "$disabled" in
    *"$name"*) ;;
    *)
      echo "disabled toolsets are missing ${name}: ${disabled}" >&2
      exit 1
      ;;
  esac
done

approval="$(solomon_exec hermes config get skills.write_approval)"
case "$approval" in
  *true*) ;;
  *)
    echo "skills.write_approval did not stick: ${approval}" >&2
    exit 1
    ;;
esac

if [[ -f "$HOME_DIR/.hermes/auth.json" ]]; then
  chown "$ACCOUNT:$ACCOUNT" "$HOME_DIR/.hermes/auth.json"
  chmod 600 "$HOME_DIR/.hermes/auth.json"
  systemctl restart solomon.service
fi

uid="$(id -u "$ACCOUNT")"
loginctl enable-linger "$ACCOUNT"
systemctl start "user@${uid}.service" || true
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if [[ -S "/run/user/${uid}/bus" ]]; then
    break
  fi
  sleep 1
done
if [[ ! -S "/run/user/${uid}/bus" ]]; then
  echo "No user bus for ${ACCOUNT} at /run/user/${uid}/bus, so the Hermes service was not installed." >&2
  exit 1
fi

sudo -u "$ACCOUNT" -H env \
  XDG_RUNTIME_DIR="/run/user/${uid}" \
  DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
  bash -c 'export PATH="$HOME/.local/bin:$PATH"; exec hermes gateway install --if-missing --start-now --start-on-login' \
  </dev/null

if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi

cat <<'EOF'

Solomon is installed. The service listens on port 8000.
SQLite is /var/lib/solomon/solomon.db and this script does not delete it.

Join the tailnet from this VM. Do not pass an auth key:

  sudo tailscale up

Leave Funnel off.

If ~/.hermes/auth.json is not there yet, stop. The person who owns the Nous
account runs this as the solomon user, at the keyboard:

  hermes auth add nous --type oauth
  chmod 600 ~/.hermes/auth.json
  sudo systemctl restart solomon

Then check:

  hermes portal info
  hermes doctor
  hermes config get model.default
  systemctl is-active solomon
  hermes gateway status

EOF
