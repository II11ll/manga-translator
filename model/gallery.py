from sqlalchemy import Column, Integer, Text, JSON
from model.base import Base
from sqlalchemy.orm import relationship
class Gallery(Base):
    __tablename__ = 'gallery'
    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_name = Column(Text)
    img_num = Column(Integer)
    create_time = Column(Text)
    author_name = Column(Text)
    source_url = Column(Text)
    pic_md = Column(Text) # 图片的md5值
    location_json = Column(JSON)
    line_txt = Column(Text)
    width = Column(Integer)
    height = Column(Integer)
    tag = Column(Text)
    blocks = relationship("Block", back_populates="gallery", cascade='all, delete, delete-orphan')