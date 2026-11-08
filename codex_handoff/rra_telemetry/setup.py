from glob import glob
from setuptools import find_packages, setup

setup(
    name='rra_telemetry',
    version='0.1.0',
    packages=find_packages(exclude=('test',)),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/rra_telemetry']),
        ('share/rra_telemetry', ['package.xml']),
        ('share/rra_telemetry/launch', glob('launch/*.launch.py')),
        ('share/rra_telemetry/config', glob('config/*.yaml')),
        ('share/rra_telemetry/scripts', glob('scripts/*.sh')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Equipo RRA',
    maintainer_email='rra@example.invalid',
    description='Observador local del estado MAVROS para RRA',
    license='Apache-2.0',
    entry_points={'console_scripts': [
        'state_observer = rra_telemetry.state_observer:main',
        'telemetry_simulator = rra_telemetry.telemetry_simulator:main',
    ]},
)
