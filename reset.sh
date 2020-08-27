#!/bin/bash

# Remove the installation
sudo pip3 -y uninstall ufotest

# Remove the config
sudo rm $HOME/.ufotest/*

# Install the new version
sudo make install

# remove the installation folder
sudo rm -rf ./install/*
