sudo apt install openjdk-11-jdk
sudo apt install openjdk-17-jdk
sudo apt install openjdk-21-jdk

git clone https://github.com/jenv/jenv.git ~/.jenv
echo 'export PATH="$HOME/.jenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(jenv init -)"' >> ~/.bashrc
source ~/.bashrc

jenv add /usr/lib/jvm/java-11-openjdk-amd64
jenv add /usr/lib/jvm/java-17-openjdk-amd64
jenv add /usr/lib/jvm/java-21-openjdk-amd64
