const express = require("express");
const { Router } = require("express");

function initializeApp(config) {
  return express();
}

class AppServer {
  constructor(port) {
    this.port = port;
  }

  start() {
    console.log(`Listening on ${this.port}`);
  }
}

const handleRequest = (req, res) => {
  res.send("OK");
};

export default function createServer(port) {
  return new AppServer(port);
}
