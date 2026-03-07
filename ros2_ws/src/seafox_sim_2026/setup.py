from setuptools import setup
import os
from glob import glob

package_name = 'seafox_sim_2026'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),

    ('share/' + package_name, ['package.xml']),

    (os.path.join('share', package_name, 'launch'),
        glob('launch/*.py')),

    (os.path.join('share', package_name, 'urdf'),
        glob('seafox_sim_2026/urdf/*.urdf')),

    (os.path.join('share', package_name, 'models'),
        glob('seafox_sim_2026/models/*.stl')),

    (os.path.join('share', package_name, 'rviz'),
        glob('seafox_sim_2026/rviz/*.rviz')),
],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ever',
    maintainer_email='ever@todo.todo',
    description='Seafox ROV simulation',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'depth_tf_node = seafox_sim_2026.depth_tf_node:main',
            'force_visualizer_node = seafox_sim_2026.force_visualizer_node:main',
        ],
    },
)