## Self-hosting

You can also download our processed full planet Btrfs images if you want to self-host yourself. Details can be found on [GitHub](https://github.com/hyperknot/openfreemap).

Start by copying `config/linux_host/config.sample.jsonc` to a named config such as `config/linux_host/self-hosted.jsonc`, then fill out your domain, certificate settings, `areas` (use `["monaco"]` first, then `["planet", "monaco"]`), and `auto_update` before running `./linux_host/deploy_linux_host.py --config self-hosted`.
