from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import Session, relationship, backref, joinedload_all
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.collections import attribute_mapped_collection

Base = declarative_base()


class TreeNode(Base):
    __tablename__ = 'tree'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('id'))
    name = Column(String(50), nullable=False)

    children = relationship(
        'TreeNode',

        # 级联删除
        cascade='all, delete-orphan',

        # 在join条件中必须加入'remote_side'
        backref=backref('parent', remote_side=id),

        # 子属性在字典中以"name"做键来表示
        collection_class=attribute_mapped_collection('name'),
    )

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

    def __repr__(self):
        return 'TreeNode(name=%r, id=%r, parent_id=%r)' %(
            self.name,
            self.id,
            self.parent_id
        )

    def dump(self, _indent=0):
        return "   " * _indent + repr(self) + \
            "\n" + \
            "".join([
                c.dump(_indent + 1)
                for c in self.children.values()
            ])

    
if __name__ == '__main__':
    engine = create_engine("sqlite://", echo=True)

    def msg(msg, *args):
        msg = msg % args
        print("\n\n\n" + '-' * len(msg.split("\n")[0]))
        print(msg)
        print("-" * len(msg.split('\n')[0]))

    msg('Creating Tree Table:')

    Base.metadata.create_all(engine)

    session = Session(engine)

    node = TreeNode('rootnode')
    TreeNode('node1', parent=node)
    TreeNode('node3', parent=node)

    node2 = TreeNode('node2')
    TreeNode('subnode1', parent=node2)
    node.children['node2'] = node2
    TreeNode('subnode2', parent=node.children['node2'])

    msg("Creating new tree structure:\n%s", node.dump())

    msg("flush + commit:")

    session.add(node)
    session.commit()

    msg('Tree After Save:\n %s', node.dump())

    TreeNode('node4', parent=node)
    TreeNode('subnode3', parent=node.children['node4'])
    TreeNode('subnode4', parent=node.children['node4'])
    TreeNode('subsubnode1', parent=node.children['node4'].children['subnode3'])

    # 将一个node和parent解除关联，将会出发"delete-orphan"
    del node.children['node1']
    msg('Removal node1. flush + commit:')
    session.commit()

    msg("Tree after save:\n%s", node.dump())

    msg("Empty out session entirely, selecting tree on root, using "
        "eager loading to join four levels deep")
    session.expunge_all()

    node = session.query(
        TreeNode
    ).options(
        joinedload_all(
            'children', "children",
            "children", "children"
        )
    ).filter(
        TreeNode.name == 'rootnode'
    ).first()
    
    msg("Full Tree:\n%s", node.dump())

    msg("Marking root node as deleted, flush + commit:")

    session.delete(node)
    session.commit()