# Prompt given to every agent run (AssemblyWorld test)

The first paragraph is AssemblyWorld's task text verbatim (App. A.2, "Task Instructions"),
with the no-reference line, which is what the paper used for Fantastic Breaks. The second is
its execution instruction, paraphrased because the paper does not quote it. The third tells
the agent how to call our rebuilt tools, which the paper's harness did through MCP instead.
`{TASK}` and `{ENV}` are filled in per run.

---

Assemble the supplied parts into a coherent object. No manual or reference image is supplied. Infer the assembly from the part geometry alone. Inspect connections from multiple camera views using capture_scene, correct gaps, orientation and obvious interpenetration, and report uncertainties. Do not claim computed accuracy or physical stability without evidence. Before finishing, check whether all supplied parts have been incorporated into the assembly.

Interact only through the environment tools below. Do not read, list or open any other file or folder (including the part mesh files, any repository, notes or earlier experiments), do not reset the scene, and do not start other agents. You may view the images that capture_scene returns, using your Read tool on the path it prints. You have 60 minutes.

The tools are one command line; every call prints a JSON result:

    PYOPENGL_PLATFORM=osmesa python3 {ENV} --task {TASK} <tool> [arguments]

    start_episode                          call once first
    list_objects
    get_object PART                        centre position, orientation quaternion (w,x,y,z), box extents
    get_scene                              conventions, groups, camera, every part's pose
    capture_scene                          renders a 1024x768 view and prints the PNG path; Read it to see it
    move_camera [--yaw D] [--pitch D] [--zoom F] [--pan-x U] [--pan-y U] [--reset]
                                           orbit by degrees, zoom by a factor (>1 closer), pan in scene units
                                           along the image's right/up; --reset frames all parts
    translate_objects IDS --vec X Y Z [--frame world|camera]
    rotate_objects IDS --angles AX AY AZ [--frame world|camera] [--pivot X Y Z]
                                           degrees, applied X then Y then Z; default pivot is the mean centre
    set_object_pose PART [--position X Y Z] [--quat W X Y Z]
    group_objects NAME IDS / ungroup_objects NAME
                                           move several parts together; grouping does not snap them
    finish                                 call once at the end; saves the assembly that gets scored

World up is +Z; units are scene units. In camera frame, X is image right, Y is image up, Z
points back towards the camera. When you are done, call finish, then report what you did and
what you are unsure of.
