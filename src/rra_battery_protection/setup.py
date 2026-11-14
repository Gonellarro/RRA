from glob import glob
from setuptools import setup
import os

package_name = "rra_battery_protection"
setup(name=package_name, version="0.1.0", packages=[package_name],
      data_files=[
          ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
          ("share/" + package_name, ["package.xml", "README.md"]),
          (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
          (os.path.join("share", package_name, "ardupilot"), glob("ardupilot/*.lua")),
          (os.path.join("share", package_name), ["rra-power-shutdown.service"]),
          (os.path.join("share", package_name, "scripts"), glob("scripts/*.sh")),
      ], install_requires=["setuptools"], zip_safe=True,
      description="RRA electronics battery low-voltage protection logic",
      entry_points={"console_scripts": [
          "rra-battery-sim = rra_battery_protection.sim:main",
          "rra-battery-monitor-dry-run = rra_battery_protection.monitor:main",
          "rra-power-shutdown-dry-run = rra_battery_protection.power_shutdown:main",
          "rra-power-shutdown = rra_battery_protection.power_shutdown:main",
          "rra-power-shutdown-protocol-smoke = rra_battery_protection.protocol_smoke:main",
      ]})
