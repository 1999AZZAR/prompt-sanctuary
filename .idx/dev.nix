{ pkgs, ... }: {
  channel = "stable-23.11";

  # Core system packages
  packages = [
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.python3Packages.virtualenv
    pkgs.git
    pkgs.curl
    pkgs.wget
    pkgs.busybox
    pkgs.speedtest-cli
    pkgs.neofetch
    pkgs.ripgrep
    pkgs.fd
    pkgs.tree
  ];

  # Development tools
  env = {
    PYTHONPATH = "${pkgs.python3}/lib/python3.11/site-packages";
    LANG = "en_US.UTF-8";
    VIRTUAL_ENV = ".venv";
    PATH = [ "\${VIRTUAL_ENV}/bin" ];
  };

  idx = {
    # Essential development extensions
    extensions = [
      "ms-python.python"
      "ms-python.vscode-pylance"
      "njpwerner.autodocstring"
      "streetsidesoftware.code-spell-checker"
      "eamodio.gitlens"
      "ms-python.black-formatter"
      "ms-python.flake8"
    ];

    workspace = {
      onCreate = {
        install = ''
          python -m venv .venv
          source .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install black flake8 pylint pytest
        '';
      };
      
      onStart = {
        welcome = "echo 'Development environment ready!'";
      };
    };

    previews = {
      enable = true;
      previews = {
        web = {
          command = [ "./devserver.sh" ];
          env = { 
            PORT = "$PORT";
            PYTHONPATH = "$PYTHONPATH";
            VIRTUAL_ENV = "$VIRTUAL_ENV";
          };
          manager = "web";
        };
      };
    };
  };
}