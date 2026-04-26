# Pacote de instalação

Execute `python install/install.py` a partir da raiz do repositório.

Esse pacote monta o sistema na raiz do projeto, usando a pasta pai de `install/` como destino.

O instalador decide em cascata: `backend do modelo -> presença de CUDA -> wheel compatível do PyTorch`. Se não houver compatibilidade, ele preserva o modo CPU/sem PyTorch.
