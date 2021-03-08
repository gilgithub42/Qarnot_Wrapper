FROM robocarstore/donkeycar
RUN apt-get update && apt-get upgrade -y \
	&& apt-get install vim git python3 wget curl unzip -y \
	&& rm -rf /var/lib/apt/lists/*
RUN wget https://github.com/tawnkramer/gym-donkeycar/releases/download/v21.02.20/DonkeySimLinux.zip \
	&& unzip DonkeySimLinux.zip -d DonkeySimLinux \
	&& cp DonkeySimLinux/DonkeySimLinux/donkey_sim.x86_64 . \
	&& rm -rf DonkeySimLinux DonkeySimLinux.zip
RUN /usr/local/bin/python -m pip install --upgrade pip \
	&& pip install Keras  Pillow  docopt  gym  imageio  imgaug \
	matplotlib  numpy  opencv_python  paho_mqtt  pandas  pickle-mixin \
	prettytable  progress  pyfiglet  pyzmq  requests  scikit_image \
	setuptools  simple_pid  tensorflow  torch  tornado  typing_extensions \
	GitPython  gym  matplotlib  numpy  pandas scikit-learn==0.23.2 sklearn \
	sklearn_deap  torch  tqdm
RUN ls && git clone https://github.com/ezalos/1st_DQN.git /dqn \
	&& cd /dqn && git checkout Louis 