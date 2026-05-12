# potatao (zero) station

Raspberry Pi Zero used to have outside world connection and see others potatao phones (RP pico)
send messanges and send data to local pc with AI to translate voice 

# required developing software

UV: python library management system

steps of usage:

1. download uv on your developing device:

   sudo pacman -S uv (Arch Linux)
   brew install uv (Mac os)

2. check the UV version
   
   uv --version

3. init uv workspace (parent toml) (tip: this step has already done in this project, skip it.)
   
   uv init

4. modify the pyproject.toml (this step has already done )

  ## 4.1 add sub-modules
  1. if you want to add a sub-module as a service (your back-end application), use the command below:
   
     uv init --app [your service folder name]

  2. if you want to add a sub-module as lib, use the command below:

      uv init --lib [your lib folder name]

5. download library packages
     
     uv sync --all-packages

6. start the back-end service
     
    uv run uvicorn service.app:app --reload