from setuptools import find_packages, setup

package_name = 'seafox_rov_2026'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    ('share/' + package_name + '/launch', ['launch/control_launch.py']),
],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ever',
    maintainer_email='ever.alcaraz@cetys.edu.mx',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'cameras_publisher = seafox_rov_2026.cameras.camerasPublisher:main',
                #control scripts
                'joystick_reader = seafox_rov_2026.control.a_joystick_reader:main',
                'joystick_to_twist = seafox_rov_2026.control.b_joystick_to_twist:main',
                'twist_to_pwm = seafox_rov_2026.control.f_twist_to_pwm:main',
        ],
    },
)
