import bpy
import ast
import time


class Timer(object):  # pragma: no cover
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        if self.name:
            print('[%s]' % self.name,)
        print('Elapsed: %s' % (time.time() - self.tstart))


# size (x,y,z) location (x,y,z)
def add_cube(size, location, quat, i):
    bpy.ops.mesh.primitive_cube_add(radius=1, view_align=False, enter_editmode=False, location=location,
                                    layers=(True, False, False, False, False, False, False, False, False, False, False,
                                            False, False, False, False, False, False, False, False, False))
    bpy.context.object.name = "Cube" + str(i)
    bpy.context.object.dimensions = size
    bpy.context.object.rotation_mode = "QUATERNION"
    bpy.context.object.rotation_quaternion = quat
    # mat = create_new_material("Cube" + str(i) + "_mat", (0.1*i, 0, 0, 1))
    # bpy.context.object.data.materials.append(mat)


def set_camera(location, quat):
    camera = bpy.context.scene.camera
    camera.location = location
    camera.rotation_quaternion = quat


def create_new_material(name, color):
    bpy.data.materials.new(name=name)
    # get material
    mat = bpy.data.materials[name]
    # remove all previous shaders
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)

    # add emission node
    node_emission = nodes.new(type='ShaderNodeEmission')
    node_emission.inputs[0].default_value = color  # color rgba
    node_emission.inputs[1].default_value = 1.0  # strength

    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    links = mat.node_tree.links
    link = links.new(node_emission.outputs[0], node_output.inputs[0])
    return mat


def setup_camera():
    camera = bpy.context.scene.camera
    # for this see https://blender.stackexchange.com/questions/118056/how-to-use-quaternions-coming-from-ros
    camera.scale = (1, -1, -1)
    camera.rotation_mode = "QUATERNION"
    cam = bpy.data.cameras["Camera"]
    # this part sets the measured intrinsic calibration matrix K
    # see https://blender.stackexchange.com/questions/883/how-to-set-a-principal-point-for-a-camera and
    # https://blender.stackexchange.com/questions/58235/what-are-the-units-for-camera-shift for more information
    # The principal point in pixels is 306.86169342 and 240.94547232 in pixels and the below in blender units, which are
    # percentage of the biggest width in pixels. So shift_x of 1 will shift the principal point by 620 pixels, so will
    # a shift_y of 1, so be cautious of this
    cam.shift_x = (640 / 2 - 306.86169342) / 640
    cam.shift_y = (480 / 2 - 240.94547232) / 640
    # for sensor width see here: https://www.ovt.com/download/sensorpdf/207/OmniVision_OV9282.pdf
    cam.sensor_width = 3.896
    cam.lens = 610.55992534 / 640 * cam.sensor_width


def setup_speedup():
    # speed up
    # bpy.context.scene.world.light_settings.samples = 1
    # Big tiles better for GPU small better for CPU
    bpy.data.scenes['Scene'].render.tile_x = 1024
    bpy.data.scenes['Scene'].render.tile_y = 1024
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
    # CPU
    bpy.context.user_preferences.addons['cycles'].preferences.devices[0].use = False
    # GPU
    bpy.context.user_preferences.addons['cycles'].preferences.devices[1].use = True


def setup_scene():
    # needed for rendering the whole cube with one color
    # bpy.data.scenes['Scene'].render.engine = "CYCLES"
    bpy.context.scene.render.resolution_x = 640
    bpy.context.scene.render.resolution_y = 480
    bpy.context.scene.render.resolution_percentage = 100


def setup(box_positions):
    setup_camera()
    # setup_speedup()
    setup_scene()

    objs = bpy.data.objects
    objs.remove(objs["Cube"], True)
    box_sizes = [(0.349, 0.213, 0.117)]

    for i, box_position in enumerate(box_positions):
        translation, quat_ros = list_to_tuples(box_position)
        quat = ros_to_blender_quat(quat_ros)
        add_cube(box_sizes[i], translation, quat, i)


def list_to_tuples(l):
    return tuple(l[:3]), tuple(l[3:])


# blender uses wxyz and ros xyzw
def ros_to_blender_quat(qaut):
    return qaut[-1], qaut[0], qaut[1], qaut[2]


def main():
    with open('data/camera1_positions.txt') as f:
        lines = f.readlines()
    camera_positions = [ast.literal_eval(line) for line in lines]
    with open('data/box_positions.txt') as f:
        lines = f.readlines()
    box_positions = [ast.literal_eval(line) for line in lines]
    setup(box_positions)
    print(len(camera_positions))

    for i, camera_position in enumerate(camera_positions):
        with Timer("Rendering"):
            translation, quat_ros = list_to_tuples(camera_position)
            quat = ros_to_blender_quat(quat_ros)
            set_camera(translation, quat)
            # print(translation)
            # print(quat)
            bpy.context.scene.render.filepath = "data/images/cube" + str(i) + ".png"
            bpy.ops.render.render(use_viewport=True, write_still=True)


if __name__ == "__main__":
    main()
