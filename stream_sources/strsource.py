import configparser as cfp

class strsource:
  def __init__(self):
    self.config = cfp.ConfigParser()
    self.config.read('secure-data.ini')
