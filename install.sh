#!/bin/bash

echo -e "\033[34mDo you want to install or remove the bot? (install/remove): \033[0m"
read -p "" ACTION

case $ACTION in
  [Ii][Nn][Ss][Tt][Aa][Ll][Ll])
    echo -e "\033[34mUpdating system...\033[0m"
    sudo apt update

    echo -e "\033[34mInstalling Python and required tools...\033[0m"
    sudo apt install -y python3 python3-pip python3-venv git

    echo -e "\033[34mCloning project from your GitHub fork...\033[0m"
    REPO_URL="https://github.com/damakhlol/sub-to-link.git"
    REPO_DIR="/opt/sub-to-link"

    if [ -d "$REPO_DIR" ]; then
      sudo rm -rf "$REPO_DIR"
    fi

    sudo git clone "$REPO_URL" "$REPO_DIR"

    sudo chown -R $USER:$USER "$REPO_DIR"
    cd "$REPO_DIR"

    clear
    read -p "Please enter your Telegram Bot Token: " BOT_TOKEN

    echo "BOT_TOKEN = \"$BOT_TOKEN\"" > config.py

    echo -e "\033[34mCreating virtual environment...\033[0m"
    python3 -m venv venv

    echo -e "\033[34mActivating virtual environment and installing packages...\033[0m"
    source venv/bin/activate
    pip install python-telegram-bot==20.7 requests

    echo -e "\033[34mRunning bot in background...\033[0m"
    nohup python main.py > /dev/null 2>&1 &

    echo -e "\033[32mBot started successfully!\033[0m"
    ;;
  [Rr][Ee][Mm][Oo][Vv][Ee])
    echo -e "\033[34mFinding and stopping bot processes...\033[0m"
    PIDS=$(ps aux | grep '[p]ython main.py' | awk '{print $2}')
    if [ -n "$PIDS" ]; then
      for PID in $PIDS; do
        kill $PID
        echo -e "\033[34mStopped process with PID $PID\033[0m"
      done
    else
      echo -e "\033[33mNo running bot processes found\033[0m"
    fi
    ;;
  *)
    echo -e "\033[31mInvalid option. Please choose 'install' or 'remove'.\033[0m"
    exit 1
    ;;
esac
