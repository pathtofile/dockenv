"""
Test dockenv
"""
from unittest.mock import patch
from dockenv import dockenv
from .mocked_types import MockedImage


def test_get_venv_name_nolatest():
    """
    Test get_venv_name matches on name without end tag
    """
    expected = "myenv"
    input_param = f"dockenv-{expected}"
    output = dockenv.get_venv_name(input_param)
    assert expected == output


def test_get_venv_name_latest():
    """
    Test get_venv_name matches on name with end tag
    """
    expected = "myenv"
    test_input = f"dockenv-{expected}:latest"
    result = dockenv.get_venv_name(test_input)
    assert expected == result


@patch("docker.models.images.ImageCollection.list")
def test_local_image_exists_found(mocked_imagelist):
    """
    Test local_image_exists finds image matching name
    """
    test_input = "dockenv-aaa"
    result_imagelist = [
        MockedImage(["python3:latest"]),
        MockedImage(["dockenv-bbb:latest", f"{test_input}:latest"]),
        MockedImage(["dockenv-ccc:latest"])
    ]
    mocked_imagelist.return_value = result_imagelist
    assert dockenv.local_image_exists(test_input)


@patch("docker.models.images.ImageCollection.list")
def test_local_image_exists_found_tag(mocked_imagelist):
    """
    Test local_image_exists finds image matching name and tag
    """
    test_input = "dockenv-aaa"
    test_input_tag = "mytag"
    result_imagelist = [
        MockedImage(["python3:latest"]),
        MockedImage(["dockenv-bbb:latest", f"{test_input}:{test_input_tag}"]),
        MockedImage(["dockenv-ccc:latest"])
    ]
    mocked_imagelist.return_value = result_imagelist
    assert dockenv.local_image_exists(test_input, tagname=test_input_tag)


@patch("docker.models.images.ImageCollection.list")
def test_local_image_exists_notfound(mocked_imagelist):
    """
    Test local_image_exists return False when image not in list
    """
    test_input = "dockenv-ccc"
    result_imagelist = [
        MockedImage(["python3:latest"]),
        MockedImage(["dockenv-aaa:latest", "dockenv-bbb:latest"]),
        MockedImage(["dockenv-cccc:latest"])
    ]
    mocked_imagelist.return_value = result_imagelist
    assert not dockenv.local_image_exists(test_input)


@patch("docker.models.images.ImageCollection.list")
def test_local_image_exists_different_tag(mocked_imagelist):
    """
    Test local_image_exists return False when image exists,
    but tag is different to tag passed in
    """
    test_input = "dockenv-ccc"
    test_input_tag = "mytag"
    result_imagelist = [
        MockedImage(["python3:latest"]),
        MockedImage(["dockenv-aaa:latest", f"dockenv-{test_input}:badtag"]),
        MockedImage(["dockenv-cccc:latest"])
    ]
    mocked_imagelist.return_value = result_imagelist
    assert not dockenv.local_image_exists(test_input, tagname=test_input_tag)


@patch("docker.models.images.ImageCollection.list")
def test_local_image_exists_empty(mocked_imagelist):
    """
    Test local_image_exists return False when list is empty
    """
    test_input = "dockenv-aaa"
    mocked_imagelist.return_value = []
    assert not dockenv.local_image_exists(test_input)


@patch("docker.models.images.ImageCollection.list")
def test_get_local_container_missing(mocked_imagelist):
    """
    Test get_local_container returns None when image not in list
    """
    test_input = "dockenv-ddd"
    result_imagelist = [
        MockedImage(["python3:latest"]),
        MockedImage(["dockenv-aaa:latest", f"dockenv-bbb:latest"]),
        MockedImage(["dockenv-cccc:latest"])
    ]
    mocked_imagelist.return_value = result_imagelist
    assert dockenv.get_local_container(test_input) is None


@patch("docker.models.images.ImageCollection.list")
@patch("docker.models.containers.ContainerCollection.get")
def test_get_local_container_found(mocked_containerget, mocked_imagelist):
    """
    Test get_local_container returns a container than matches name
    """
    test_input = "dockenv-aaa"

    result_imagelist = [
        MockedImage(["python3:latest"]),
        MockedImage(["dockenv-aaa:latest", f"dockenv-bbb:latest"]),
        MockedImage(["dockenv-cccc:latest"])
    ]
    mocked_imagelist.return_value = result_imagelist
    expected_result = "myobject"
    mocked_containerget.return_value = expected_result

    assert dockenv.get_local_container(test_input) is expected_result
    mocked_containerget.assert_called_once_with(test_input)
