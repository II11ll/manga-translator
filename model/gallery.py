from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, Text
class Base(DeclarativeBase):
    pass
class Gallery(Base):
    __tablename__ = 'gallery'
    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_name = Column(Text)
    img_num = Column(Integer)
    create_time = Column(Text)
    author_name = Column(Text)
    source_url = Column(Text)
    pic_md = Column(Text) # 图片的md5值