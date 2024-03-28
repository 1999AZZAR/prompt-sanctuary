{pkgs, ...}: {
  packages = [pkgs.speedtest-cli pkgs.neofetch pkgs.htop pkgs.eza];
  env = {};
  idx = {
    workspace = {
      # Runs when a workspace is first created with this `dev.nix` file
      onCreate = {
        create-venv = ''
          python -m venv sanctuary
          source sanctuary/bin/activate
          pip install -r requirements.txt
        '';
      };
    };
  };
}
