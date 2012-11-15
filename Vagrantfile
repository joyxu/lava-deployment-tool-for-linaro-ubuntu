# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "ubuntu-precise"
  # Use more reliable virtual NIC implementation, see
  # https://github.com/mitchellh/vagrant/issues/516#issuecomment-3998630
  config.vm.customize(["modifyvm", :id, "--nictype1", "Am79C973"])
  config.vm.forward_port 8000, 8000 # to use Django server
  config.vm.forward_port 80, 8080   # to use Apache
  config.vm.provision :shell, :path => "vagrant-bootstrap"
end
