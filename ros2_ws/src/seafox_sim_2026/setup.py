from setuptools import find_packages, setup

package_name = 'seafox_sim_2026'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        ('share/seafox_sim_2026/launch', ['launch/display.launch.py']),
        ('share/seafox_sim_2026/models', ['seafox_sim_2026/models/rov.stl']),
        ('share/seafox_sim_2026/urdf', ['seafox_sim_2026/urdf/rov.urdf']),
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
                'depth_tf_node = seafox_sim_2026.depth_tf_node:main',
                'force_visualizer_node = seafox_sim_2026.force_visualizer_node:main',
            ],
        },
)
