import os
from typing import Any, Final

from frappe.config import ConfigHandler


class Benched:
	def __init__(self, path: str | None = None, parent_path: str | None = None):
		self.path = (
			path
			or os.environ.get(f"FRAPPE_{self.__class__.__name__.upper()}_PATH")
			or (os.path.join(parent_path, self.__class__.__name__.lower()) if parent_path else None)
			# only for Bench class ...
			or (
				# TODO: legacy, remove
				os.environ.get("FRAPPE_BENCH_ROOT") if isinstance(self, Bench) else None
			)
			or (
				# TODO: unsave relative reference, remove
				os.path.realpath(
					os.path.join(os.path.dirname(__file__), "..", "..", "..")
					if isinstance(self, Bench)
					else None
				)
			)
			or (os.path.expanduser("~/frappe-bench") if isinstance(self, Bench) else None)
		)
		if self.path is None:
			raise ValueError(f"Unable to determine path for {self.__class__.__name__}")


class Frapped:
	def __bool__(self):
		return self._is_frapped()

	def _is_frapped(self):
		return os.path.isdir(self.python_path) and os.path.exists(self.python_path, ".frappe")


class Apps(Benched):
	def __init__(self, path: str | None = None, parent_path: str | None = None):
		super().__init__(path, parent_path)
		self._apps = None

	class App(Frapped):
		def __init__(self, name: str, path: str):
			self.name = name
			self.path = path
			self.python_path = os.path.join(self.path, self.name)
			self._modules = None

		class Module(Frapped):
			def __init__(self, name: str, path: str):
				self.name = name
				self.path = path
				self.python_path = path

		@property
		def modules(self) -> dict[str, Module]:
			if self._modules is None:
				self._modules = {
					d: module
					for d in os.listdir(self.python_path)
					if (module := self.Module(d, self.python_path)) and module
				}
			return self._modules

		def __iter__(self):
			return iter(self.modules.values())

		def __getitem__(self, key):
			return self.modules[key]

	@property
	def apps(self) -> dict[str, App]:
		if self._apps is None:
			self._apps = {d: app for d in os.listdir(self.path) if (app := self.App(d, self.path)) and app}
		return self._apps

	def __iter__(self):
		return iter(self.apps.values())

	def __getitem__(self, key):
		return self.apps[key]


class Logs(Benched):
	def __init__(self, path: str | None = None, parent_path: str | None = None):
		super().__init__(path, parent_path)

	def get_log_file(self, log_type: str):
		return os.path.join(self.path, f"{log_type}.log")


class Run(Benched):
	def __init__(self, path: str | None = None, parent_path: str | None = None):
		super().__init__(
			path
			# config is the legacy naming of this folder; a misnomer
			or (os.path.join(parent_path, "config") if parent_path else None),
			parent_path,
		)


class Sites(Benched, ConfigHandler):
	ALL_SITES: Final = "__all-sites__"

	def __init__(self, path: str | None = None, parent_path: str | None = None, site_name: str | None = None):
		Benched.__init__(self, path, parent_path)
		ConfigHandler.__init__(self, os.path.join(self.path, "common_site_config.json"))
		self._sites = None
		self.site_name = (
			site_name or os.environ.get("FRAPPE_SITE") or self.common_site_config.get("default_site")
		)
		self._iterator = None

	class Site(ConfigHandler):
		def __init__(self, name: str, path: str):
			self.name = name
			self.path = path
			ConfigHandler.__init__(self, os.path.join(self.path, "site_config.json"))

	def add_site(self, site_name: str):
		site_path = os.path.join(self.path, site_name)
		os.makedirs(site_path, exist_ok=True)
		self.sites[site_name] = self.Site(site_name, site_path)

	def remove_site(self, site_name: str):
		if site_name in self.sites:
			del self.sites[site_name]
			# site_path = os.path.join(self.path, site_name)
			# Note: This doesn't actually delete the site directory, just removes it from the sites dict
			# Actual deletion should be handled separately with proper safeguards

	@property
	def common_site_config(self) -> dict[str, Any]:
		return self.config

	def update_common_site_config(self, updates: dict[str, Any]):
		self.update_config(updates)

	def get_site_config(self, site_name: str) -> dict[str, Any]:
		site = self[site_name]
		if not site:
			raise ValueError(f"Site {site_name} not found")

		combined_config = self.common_site_config.copy()
		combined_config.update(site.config)
		return combined_config

	def get_current_site_config(self) -> dict[str, Any]:
		if not self.site_name:
			raise NotImplementedError("Sites was not initialized with a site_name")
		return self.get_site_config(self.site_name)

	@property
	def sites(self) -> dict[str, Site]:
		if self._sites is None:
			self._sites = {}

			def _process(site_name, site_path):
				if os.path.isdir(site_path) and os.path.exists(os.path.join(site_path, "site_config.json")):
					self._sites[site_name] = self.Site(site_name, site_path)

			if self.site_name and self.site_name != self.ALL_SITES:
				site_path = os.path.join(self.path, self.site_name)
				_process(self.site_name, site_path)
			elif self.site_name == self.ALL_SITES:
				for site_name in os.listdir(self.path):
					site_path = os.path.join(self.path, site_name)
					_process(site_name, site_path)
		return self._sites

	def __iter__(self):
		return iter(self.sites.values())

	def __next__(self):
		if self._iterator is None:
			self._iterator = iter(self.sites.values())
		try:
			return next(self._iterator)
		except StopIteration:
			self._iterator = None
			raise

	def __getitem__(self, key):
		return self.sites[key]


class Bench(Benched):
	def __init__(self, path: str | None = None, site_name: str | None = None):
		super().__init__(path)
		self.apps = Apps(parent_path=self.path)
		self.logs = Logs(parent_path=self.path)
		self.run = Run(parent_path=self.path)
		self.sites = Sites(parent_path=self.path, site_name=site_name)
