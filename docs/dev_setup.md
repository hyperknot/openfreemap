# dev setup

### macOS

On macOS, I recommend [OrbStack](https://orbstack.dev/).

I saved this function into my bash_profile. It sets up a clean x64-based Ubuntu 24.04 VM in a few seconds.

```
orb_reset() {
   orbctl delete -f ubuntu-test
   orbctl create -a amd64 ubuntu:noble ubuntu-test
}
```

I saved the following in `.ssh/config`:

```
Host orb_my
  Hostname 127.0.0.1
  Port 32222
  IdentityFile ~/.orbstack/ssh/id_ed25519
```

Create a linux_host config once (its `hosts` array should contain your VM alias,
e.g. `orb_my`), then deploy to it:

```
cp config/linux_host/config.sample.jsonc config/linux_host/orb.jsonc
# edit orb.jsonc: set "hosts": ["orb_my"], pick "areas", set "auto_update"
./linux_host/deploy_linux_host.py --config orb --host orb_my
```
