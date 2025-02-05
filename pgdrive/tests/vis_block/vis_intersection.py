from pgdrive.component.blocks.curve import Curve
from pgdrive.component.blocks.first_block import FirstPGBlock
from pgdrive.component.blocks.intersection import InterSection
from pgdrive.component.road.road_network import RoadNetwork
from pgdrive.tests.vis_block.vis_block_base import TestBlock

if __name__ == "__main__":
    test = TestBlock()
    from pgdrive.engine.asset_loader import initialize_asset_loader

    initialize_asset_loader(test)

    global_network = RoadNetwork()
    first = FirstPGBlock(global_network, 3.0, 2, test.render, test.world, 1)

    intersection = InterSection(3, first.get_socket(0), global_network, 1)
    print(intersection.construct_block(test.render, test.world))

    id = 4
    for socket_idx in range(intersection.SOCKET_NUM):
        block = Curve(id, intersection.get_socket(socket_idx), global_network, id)
        block.construct_block(test.render, test.world)
        id += 1

    intersection = InterSection(id, block.get_socket(0), global_network, 1)
    intersection.construct_block(test.render, test.world)

    test.show_bounding_box(global_network)
    test.run()
