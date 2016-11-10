#!/usr/bin/env python
import os
import shlex
import yaml
from ConfigParser import ConfigParser
from subprocess import call, PIPE
from logging import getLogger, Formatter, StreamHandler, FileHandler, DEBUG, INFO, WARNING, ERROR

# class Backup
class Backup(object):
	def __init__(self, config_file="backup.conf", targets_file="targets.yaml"):
		self._load_config(config_file, targets_file)
		self._verify_config()
		self._init_logger()
		
		self.default_fileset = {
			"include": [],
			"exclude": []
		}
	
	def _load_config(self, config_file, targets_file):
		# config
		self.config = {
			'mkdir': 'mkdir',
			'rsync': 'rsync',
			'rsyncoption': '',
			'backuphiddenfiles': True,
			'logfile': None,
			'loglevel': 'info'
		}
		parser = ConfigParser()
		parser.read(config_file)
		global_conf = dict(parser.items('global'))
		self.config = dict(self.config, **global_conf)
		
		# targets
		self.targets = {}
		with open(targets_file) as f:
			self.targets = dict(self.targets, **yaml.load(f))

	def _verify_config(self):
		# BackupRoot
		if not 'backuproot' in self.config:
			raise Exception("BackupRoot not specified in configuration file")

		# BackupHiddenFiles
		if 'backuphiddenfiles' in self.config and isinstance(self.config['backuphiddenfiles'], basestring):
			self.config['backuphiddenfiles'] = bool(self.config['backuphiddenfiles'])

	def _init_logger(self):
		self.logger = getLogger(__name__)

		formatter = Formatter(fmt='%(asctime)s [%(levelname)s] %(message)s',
				      datefmt='%Y-%m-%d %H:%M:%S')

		log_level = self.config['loglevel'].lower()
		log_level = DEBUG   if log_level == 'debug'   else\
			    INFO    if log_level == 'info'    else\
			    WARNING if log_level == 'warning' else\
			    ERROR   if log_level == 'error'   else\
			    INFO
		self.logger.setLevel(log_level)

		stream_handler = StreamHandler()
		stream_handler.setLevel(log_level)
		self.logger.addHandler(stream_handler)
		
		if self.config['logfile'] != None:
			file_handler = FileHandler(self.config['logfile'], 'a+')
			file_handler.level = log_level
			file_handler.formatter = formatter
			self.logger.addHandler(file_handler)
		
	def backup(self):
		# run backup
		for target, config in self.targets.items():
			try:
				self.logger.info("Begin backup: "+target)
				self.do_backup(target, config)
				self.logger.info("End backup: "+target)
			except Exception as e:
				self.logger.error("Error: "+str(e))

	def do_backup(self, target, config):
		# --- retrieve configs
		# RSync host
		host = config['host'] if 'host' in config else target
		# RSync destination root
		dst_conc = config['dest'] if 'dest' in config else None
		dst_root = config['backuproot'] if 'backuproot' in config else self.config['backuproot']
		dst_root = os.path.join(dst_root, target)
		# RSync option
		option = config['option'] if 'option' in config else ''
		option = ' '.join(option) if isinstance(option, list) else option
		# Backup fileset
		fileset = dict(self.default_fileset, **config['fileset'])
		# Backup hidden files
		backup_hidden_files = config['backuphiddenfiles'] if 'backuphiddenfiles' in config else self.config['backuphiddenfiles']
		# Log file
		log_file = config['log'] if 'log' in config else None

		# --- construct rsync argument
		args = []
		for incpath in fileset['include']:
			abspath = os.path.abspath(incpath)
			absdir  = os.path.dirname(abspath)
			# source
			src = host+":"+abspath
			# destination
			dst = os.path.join(dst_root, absdir[1:]) if dst_conc is None else dst_conc
			# options
			options = [option]
			if not backup_hidden_files:
				options.append("--exclude='.+'")
			for excpath in fileset['exclude']:
				if excpath.startswith(incpath):
					options.append("--exclude='"+excpath.replace(incpath+"/","")+"'")
				elif not excpath.startswith("/"):
					options.append("--exclude='"+excpath+"'")

			args.append((options, src, dst))

		# --- execute backup
		for options, src, dst in args:
			if log_file == None:
				self.logger.info("backup "+src+" to "+dst)
			else:
				self.logger.info("backup "+src+" to "+dst+", log file available at "+log_file)
			self.mkdir(dst)
			self.rsync(options, src, dst, log_file)
			self.logger.info("finished backup "+src+" to "+dst)
	
	def mkdir(self, dir):
		# mkdir command
		mkdir = self.config['mkdir']

		# executable command
		command = mkdir+" -p "+dir

		# execute
		self.logger.debug("Executing: "+command)
		retcode = call(shlex.split(command))
		self.logger.debug("command exited with code "+str(retcode))

	def rsync(self, options, src, dst, logfile=None):
		# options
		options = [ self.config['rsyncoption'] ] + options
		options = ' '.join(options)

		# rsync command
		rsync = self.config['rsync']

		# executable command
		command  = rsync+" "+options+" "+src+" "+dst

		# output
		out = open(logfile, 'a+') if logfile != None else PIPE

		# execute
		self.logger.debug("Executing: "+command)
		retcode = call(shlex.split(command), stdout=out, stderr=out)
		self.logger.debug("command exited with code "+str(retcode))
		if logfile != None: out.close()

if __name__ == '__main__':
	backup = Backup()
	backup.backup()
