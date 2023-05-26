from dateutil import parser

import os

from xml.etree import ElementTree

import zipfile

class Browser():
    """Base directory class to manage files in the input & output directories."""

    def __init__(self,homedir=None,filedir=None,filepath=None):
        """Initializes base directory class with home & file directories."""

        self.set_homedir(homedir)

        self.set_filedir(filedir)

        self.set_filepath(filepath)

    def set_homedir(self,path=None):
        """Sets the home directory for outputs."""

        if path is None:
            path = os.getcwd()

        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(os.getcwd(),path))

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        super().__setattr__("homedir",path)

    def set_filedir(self,path=None):
        """Sets the file directory for inputs."""

        if path is None:
            path = os.getcwd()

        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(os.getcwd(),path))

        if not os.path.isdir(path):
            path = os.path.dirname(path)

        super().__setattr__("filedir",path)

    def set_filepath(self,path=None):
        """Sets the file path for the cases when it is working on a single file."""

        if path is None:
            return

        if os.path.isabs(path):
            self.set_filedir(path)
        else:
            path = self.get_abspath(path,homeFlag=False)

        if os.path.isdir(path):
            super().__setattr__("filedir",os.path.dirname(path))
        else:
            super().__setattr__("filedir",os.path.dirname(path))
            super().__setattr__("filepath",path)

    def get_extended(self,path=None,extension=None):
        """Returns the path confirming extension."""

        if path is None:
            path = self.filepath

        if extension is None:
            extension = ""

        dirname = os.path.dirname(path)

        basename = os.path.basename(path)

        rootname = os.path.splitext(basename)[0]

        basename = f"{rootname}{extension}"

        return os.path.normpath(os.path.join(dirname,basename))

    def get_abspath(self,path,homeFlag=False):
        """Returns absolute path for a given relative path."""
        
        if os.path.isabs(path):
            return path
        elif homeFlag:
            return os.path.normpath(os.path.join(self.homedir,path))
        else:
            return os.path.normpath(os.path.join(self.filedir,path))

    def file_exists(self,path,homeFlag=False):

        path = self.get_abspath(path,homeFlag=homeFlag)

        return os.path.exists(path)

    def get_dirpath(self,path,homeFlag=False):
        """Returns absolute directory path for a given relative path."""

        path = self.get_abspath(path,homeFlag=homeFlag)

        if os.path.isdir(path):
            return path
        else:
            return os.path.dirname(path)

    def get_fnames(self,path=None,homeFlag=False,prefix=None,extension=None,returnAbsFlag=False,returnDirsFlag=False):
        """Return directory(folder)/file names for a given relative path."""

        if path is None:
            path = self.filedir if homeFlag is False else self.homedir
        else:
            path = self.get_dirpath(path,homeFlag=homeFlag)

        fnames = os.listdir(path)

        fpaths = [self.get_abspath(fname,homeFlag=homeFlag) for fname in fnames]

        if returnDirsFlag:

            foldernames = [fname for (fname,fpath) in zip(fnames,fpaths) if os.path.isdir(fpath)]
            folderpaths = [fpath for fpath in fpaths if os.path.isdir(fpath)]

            if prefix is None:
                if returnAbsFlag:
                    return folderpaths
                else:
                    return foldernames
            else:
                if returnAbsFlag:
                    return [folderpath for (folderpath,foldername) in zip(folderpaths,foldernames) if foldername.startswith(prefix)]
                else:
                    return [foldername for foldername in foldernames if foldername.startswith(prefix)]
        else:

            filenames = [fname for (fname,fpath) in zip(fnames,fpaths) if not os.path.isdir(fpath)]
            filepaths = [fpath for fpath in fpaths if not os.path.isdir(fpath)]

            if prefix is None and extension is None:
                if returnAbsFlag:
                    return filepaths
                else:
                    return filenames
            elif prefix is None and extension is not None:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.endswith(extension)]
                else:
                    return [filename for filename in filenames if filename.endswith(extension)]
            elif prefix is not None and extension is None:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.startswith(prefix)]
                else:
                    return [filename for filename in filenames if filename.startswith(prefix)]
            else:
                if returnAbsFlag:
                    return [filepath for (filepath,filename) in zip(filepaths,filenames) if filename.startswith(prefix) and filename.endswith(extension)]
                else:
                    return [filename for filename in filenames if filename.startswith(prefix) and filename.endswith(extension)]

    def get_fpaths(self,path=None,prefix=None,extension=None,timeref=None,timecond="before",timedetail="created",recursive=True,_list=None):

        if path is None:
            path = self.homedir

        if _list is None:
            _list = []

        fnames = os.listdir(path)

        for fname in fnames:

            fpath = os.path.join(path,fname)

            if os.path.isdir(fpath) and recursive:
                _list = self.get_fpaths(path=fpath,prefix=prefix,extension=extension,timeref=timeref,timecond=timecond,timedetail=timedetail,_list=_list)
            else:
                nameFlag = self._doesnamematch(path=fpath,prefix=prefix,extension=extension)
                timeFlag = self._doestimematch(path=fpath,reference=timeref,condition=timecond,detail=timedetail)

                if nameFlag and timeFlag:
                    _list.append(fpath)

        return _list

    def _doesnamematch(self,path,prefix=None,extension=None):

        flag = True

        path = os.path.split(path)[-1]

        fname_lower = path.lower()

        if prefix is not None:
            flag = flag and fname_lower.startswith(prefix.lower())

        if extension is not None:
            flag = flag and fname_lower.endswith(extension.lower())

        return flag

    def _doestimematch(self,path,reference=None,condition="before",detail="created"):
        """
        reference     : reference datetime.datetime to compare
        condition     : {before,after,equal}
        detail        : {created,modified}
        """

        if reference is None:
            return True

        xls_zip = zipfile.ZipFile(path)

        xml_contents = xls_zip.read("docProps/core.xml")

        et = ElementTree.fromstring(xml_contents)

        filetime = et.find(f'dcterms:{detail}',{"dcterms":"http://purl.org/dc/terms/"})
        filetime = parser.parse(filetime.text)

        reference = reference.astimezone(filetime.tzinfo)

        if condition=="before":
            return filetime<reference
        elif condition=="after":
            return filetime>reference
        elif condition=="equal":
            return filetime==reference

    @property
    def basename(self):
        """
        /home/jsmith/base.wiki --> base.wiki
        /home/jsmith/          --> jsmith
        /                      --> /
        """
        return os.path.basename(self.filepath)

    @property
    def rootname(self):
        """
        /home/jsmith/base.wiki --> base 
        """
        return os.path.splitext(self.basename)[0]

    @property
    def extension(self):
        """
        /home/jsmith/base.wiki --> .wiki 
        """
        return os.path.splitext(self.filepath)[1]