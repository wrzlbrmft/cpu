def read_obj_file(file_name):
    pass


def read_obj_files(file_names):
    for file_name in file_names:
        read_obj_file(file_name)


# main


read_obj_files(['test1.obj'])
