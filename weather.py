# weather.py version 1.2, http://fungi.yuggoth.org/weather/
# Copyright (c) 2006 Jeremy Stanley <fungi@yuggoth.org>, all rights reserved.
# Licensed per terms in the LICENSE file distributed with this software.

"""Contains various object definitions needed by the weather utility."""

version = "1.2"

class Selections:
	"""An object to contain selection data."""
	def __init__(self):
		"""Store the config, options and arguments."""
		self.config = get_config()
		self.options, self.arguments = get_options(self.config)
		if self.arguments:
			self.arguments = [(x.lower()) for x in self.arguments]
		else: self.arguments = [ None ]
	def get(self, option, argument=None):
		"""Retrieve data from the config or options."""
		if not argument: return self.options.__dict__[option]
		elif not self.config.has_section(argument):
			import sys
			sys.stderr.write("ERROR: no alias defined for " \
				+ argument + "\n")
			sys.exit(1)
		elif self.config.has_option(argument, option):
			return self.config.get(argument, option)
		else: return self.options.__dict__[option]
	def get_bool(self, option, argument=None):
		"""Get data and coerce to a boolean if necessary."""
		return bool(self.get(option, argument))

def bool(data):
	"""Coerce data to a boolean value."""
	if type(data) is str:
		if eval(data): return True
		else: return False
	else:
		if data: return True
		else: return False

def quote(words):
	"""Wrap a string in quotes if it contains spaces."""
	if words.find(" ") != -1: words = "\"" + words + "\""
	return words

def sorted(data):
	"""Return a sorted copy of a list."""
	new_copy = data[:]
	new_copy.sort()
	return new_copy

def get_url(url):
	"""Return a string containing the results of a URL GET."""
	import urllib
	return urllib.urlopen(url).read()

def get_metar(id, verbose=False):
	"""Return a summarized METAR for the specified station."""
	metar = get_url(
		"http://weather.noaa.gov/pub/data/observations/metar/decoded/" \
			+ id.upper() + ".TXT")
	if verbose: return metar
	else:
		lines = metar.split("\n")
		headings = [
			"Relative Humidity",
			"Precipitation last hour",
			"Sky conditions",
			"Temperature",
			"Weather",
			"Wind" 
			]
		output = []
		output.append("Current conditions at " \
			+ lines[0].split(", ")[1] + " (" \
			+ id.upper() +")")
		output.append("Last updated " + lines[1])
		for line in lines:
			for heading in headings:
				if line.startswith(heading + ":"):
					if line.endswith(":0"):
						line = line[:-2]
					output.append("   " + line)
		return "\n".join(output)

def get_forecast(city, st, verbose=False):
	"""Return the forecast for a specified city/st combination."""
	forecast = get_url("http://weather.noaa.gov/pub/data/forecasts/city/" \
		+ st.lower() + "/" + city.lower().replace(" ", "_") \
		+ ".txt")
	if verbose: return forecast
	else:
		lines = forecast.split("\n")
		output = []
		output.append(lines[2])
		output.append(lines[3])
		for line in lines:
			if line.startswith("."):
				output.append(line.replace(".", "   ", 1))
		return "\n".join(output)

def get_options(config):
	"""Parse the options passed on the command line."""
	import optparse
	usage = "usage: %prog [ options ] [ alias [ alias [...] ] ]"
	verstring = "%prog " + version
	option_parser = optparse.OptionParser(usage=usage, version=verstring)
	if config.has_option("default", "city"):
		default_city = config.get("default", "city")
	else: default_city = "Raleigh Durham"
	option_parser.add_option("-c", "--city",
		dest="city",
		default=default_city,
		help="the city name (ex: \"Raleigh Durham\")")
	if config.has_option("default", "forecast"):
		default_forecast = bool(config.get("default", "forecast"))
	else: default_forecast = False
	option_parser.add_option("-f", "--forecast",
		dest="forecast",
		action="store_true",
		default=default_forecast,
		help="include a local forecast")
	if config.has_option("default", "id"):
		default_id = config.get("default", "id")
	else: default_id = "KRDU"
	option_parser.add_option("-i", "--id",
		dest="id",
		default=default_id,
		help="the METAR station ID (ex: KRDU)")
	option_parser.add_option("-l", "--list",
		dest="list",
		action="store_true",
		default=False,
		help="print a list of configured aliases")
	if config.has_option("default", "conditions"):
		default_conditions = bool(config.get("default", "conditions"))
	else: default_conditions = True
	option_parser.add_option("-n", "--no-conditions",
		dest="conditions",
		action="store_false",
		default=default_conditions,
		help="disable output of current conditions (forces -f)")
	option_parser.add_option("-o", "--omit-forecast",
		dest="forecast",
		action="store_false",
		default=default_forecast,
		help="omit the local forecast (cancels -f)")
	if config.has_option("default", "st"):
		default_st = config.get("default", "st")
	else: default_st = "NC"
	option_parser.add_option("-s", "--st",
		dest="st",
		default=default_st,
		help="the state abbreviation (ex: NC)")
	if config.has_option("default", "verbose"):
		default_verbose = bool(config.get("default", "verbose"))
	else: default_verbose = False
	option_parser.add_option("-v", "--verbose",
		dest="verbose",
		action="store_true",
		default=default_verbose,
		help="show full decoded feeds")
	options, arguments = option_parser.parse_args()
	return options, arguments

def get_config():
	"""Parse the aliases and configuration."""
	import ConfigParser
	config = ConfigParser.ConfigParser()
	import os.path
	rcfiles = [
		"/etc/weatherrc",
		os.path.expanduser("~/.weatherrc"),
		"weatherrc"
		]
	import os
	for rcfile in rcfiles:
		if os.access(rcfile, os.R_OK): config.read(rcfile)
	for section in config.sections():
		if section != section.lower():
			if config.has_section(section.lower()):
				config.remove_section(section.lower())
			config.add_section(section.lower())
			for option,value in config.items(section):
				config.set(section.lower(), option, value)
	return config

def list_aliases(config):
	"""Return a formatted list of aliases defined in the config."""
	sections = []
	for section in sorted(config.sections()):
		if section.lower() not in sections and section != "default":
			sections.append(section.lower())
	output = "configured aliases..."
	for section in sorted(sections):
		output += "\n   " \
			+ section \
			+ ": --id=" \
			+ quote(config.get(section, "id")) \
			+ " --city=" \
			+ quote(config.get(section, "city")) \
			+ " --st=" \
			+ quote(config.get(section, "st"))
	return output

