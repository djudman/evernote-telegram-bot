#!/bin/sh

read_env_variable() {
	read -rp "$1=" value
	echo "export $1=\"$value\"" >> "$env_file"
}

current_dir=$(pwd)
read -rp "Install directory (default: $current_dir): " install_dir
if [ ! "$install_dir" ]; then
	install_dir="$current_dir"
else
	mkdir -p "$install_dir"
fi
echo "Installation directory: $install_dir"
export EVERNOTEBOT_DIR="$install_dir"

docker pull djudman/evernote-telegram-bot

VOLUME_NAME="evernotebot-data"

docker volume inspect $VOLUME_NAME > /dev/null 2>&1
status=$?
if [ $status -ne 0 ]; then
	echo "Volume $VOLUME_NAME created."
	docker volume create $VOLUME_NAME > /dev/null 2>&1
else
	echo "Volume $VOLUME_NAME already exists"
fi

curl https://raw.githubusercontent.com/djudman/evernote-telegram-bot/master/init.d/evernotebot --output ./evernotebot-init.d
chown root: ./evernotebot-init.d
chmod a+x ./evernotebot-init.d
mv ./evernotebot-init.d /etc/init.d/evernotebot
status=$?
if [ $status -ne 0 ]; then
	echo "Installation FAILED."
	exit 1
fi

env_file="$install_dir/.env"
if [ -f "$env_file" ]; then
	read -rp "Env file $env_file already exists. Do you want to rewrite it? (Y/n) " delete
	if [ ! "$delete" ] || [ "$delete" = "Y" ]; then
		old_env_file="$env_file.bak"
		mv "$env_file" "$old_env_file"
		touch "$env_file"

		echo "export EVERNOTEBOT_DIR=\"$install_dir\"" >> "$env_file"
		read_env_variable "EVERNOTEBOT_DEBUG"
		read_env_variable "EVERNOTEBOT_HOSTNAME"

		read_env_variable "TELEGRAM_BOT_NAME"
		read_env_variable "TELEGRAM_API_TOKEN"

		read_env_variable "EVERNOTE_BASIC_ACCESS_KEY"
		read_env_variable "EVERNOTE_BASIC_ACCESS_SECRET"

		read_env_variable "EVERNOTE_FULL_ACCESS_KEY"
		read_env_variable "EVERNOTE_FULL_ACCESS_SECRET"

		read -rp "Would you like to use mongodb as a storage (default: sqlite)? (y/N) " use_mongo
		if [ "$use_mongo" = "y" ]; then
			read_env_variable "MONGO_HOST"
		fi

		echo "source $env_file" >> ~/.bashrc
		echo "A line \"source $env_file\" added to your .bashrc"

		rm -f "$old_env_file"
		echo "File $old_env_file deleted"
	fi
fi

echo "Evernote bot successfuly installed to $install_dir"
echo "Use /etc/init.d/evernotebot start|stop|restart to start/stop/restart bot"