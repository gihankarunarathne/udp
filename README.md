# Urban Development Project -> UDP

Scripts for connecting and running flood forecasting models

# Setup macOS X

This Software is mainly focus on running on Linux. But macOS X can be setup to run it.
In order to run command line bash scripts, it want to install following libraries.

We are using **[Homebrew](https://brew.sh/)** as package management tool for macOS.
Install Homebrew by paste following line of code at a Terminal prompt.

`/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`

Then install following packages using Homebrew;

- [jq](http://brewformulas.org/Jq)
- [gnu-getopt](http://brewformulas.org/gnu-getopt)
  macOS already provides `getopt` software and installing another version in parallel can cause all kinds of trouble.
  Thus you need to have this software **first** in your PATH run:
  
  `echo 'export PATH="/usr/local/opt/gnu-getopt/bin:$PATH"' >> ~/.zshrc`