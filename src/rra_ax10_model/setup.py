from glob import glob
from setuptools import find_packages, setup

package_name = "rra_ax10_model"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/urdf", glob("urdf/*")),
        ("share/" + package_name + "/config", glob("config/*")),
        ("share/" + package_name + "/launch", glob("launch/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="RRA local",
    maintainer_email="rra-local@example.invalid",
    description="Modelo ROS preliminar y cinemática del Axial AX10",
    license="Proprietary",
    entry_points={
        "console_scripts": ["ax10_kinematics = rra_ax10_model.kinematics_node:main"],
    },
)
