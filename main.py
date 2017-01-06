from ruamel import yaml
import os
import requests
import dateutil.parser
import datetime


def pathify(string):
    return string.replace(' ', '_').replace('/', '+')


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        with open(config_file, 'r') as conf:
            data = conf.read()
            self.raw_settings = yaml.load(data, Loader=yaml.Loader)

    def save(self):
        with open(self.config_file, 'w') as conf:
            data = yaml.dump(self.raw_settings, Dumper=yaml.RoundTripDumper)
            conf.write(data)

    @property
    def token(self):
        return self.raw_settings['oauth_token']

    @token.setter
    def token(self, new_token):
        self.raw_settings['oauth_token'] = new_token

    @property
    def url(self):
        return self.raw_settings['url']

    @url.setter
    def url(self, new_url):
        self.raw_settings['url'] = new_url

    @property
    def directory(self):
        return self.raw_settings['directory']

    @directory.setter
    def directory(self, new_dir):
        self.raw_settings['directory'] = new_dir

    @property
    def term(self):
        return self.raw_settings['term']

    @term.setter
    def term(self, new_term):
        self.raw_settings['term'] = new_term

    @property
    def last_updated(self):
        return self.raw_settings['last_updated']

    @last_updated.setter
    def last_updated(self,new_last_updated):
        self.raw_settings['last_updated'] = str(new_last_updated)


class Course:
    def __init__(self, raw_data):
        self.raw_data = raw_data
        self._directory = None
        self._folders = None
        self._files = None

    @property
    def term(self):
        return self.raw_data['course_code'][-7:]

    @property
    def name(self):
        return self.raw_data['course_code'][:-8]

    @property
    def directory(self):
        if self._directory is None:
            raise ValueError("Class directory has not been set")
        else:
            return self._directory

    @property
    def folders(self):
        if self._folders is None:
            raise ValueError("Class folders have not been set")
        else:
            return self._folders

    @folders.setter
    def folders(self, new_folders):
        self._folders = new_folders

    @property
    def files(self):
        if self._files is None:
            ValueError("Class files have not been set")
        else:
            return self._files

    @files.setter
    def files(self, new_files):
        self._files = new_files

    @directory.setter
    def directory(self, new_directory):
        self._directory = new_directory

    @property
    def id(self):
        return self.raw_data['id']


class CanvasAPI():
    def __init__(self, oauth_token, url):
        self.token = oauth_token
        self.base_url = url + '/api/v1/'

    def _GET(self, url):
        response = requests.get(url,
                                params={'per_page': 30},
                                headers={'Authorization': 'Bearer ' + self.token})
        if not response.headers['Link']:
            data = response.json()
            return data
        else:
            data = response.json()
            next_url = None
            for link in response.headers['Link'].split(','):
                url, rel = link.split(';')
                rel = rel.strip()
                if rel == 'rel="next"':
                    next_url = url[1:-1]

            if not next_url:
                return data

            next_data = self._GET(next_url)
            return_data = data + next_data
            return return_data

    def get_courses(self):
        test = self._GET(self.base_url + '/courses')
        return test

    def get_folders(self, course_id):
        return self._GET(self.base_url + '/courses/' + str(course_id) + '/folders')

    def get_files(self, course_id):
        return self._GET(self.base_url + '/courses/' + str(course_id) + '/files')


def main():
    config = Config('config.yaml')
    try:
        config.last_updated
    except:
        config.last_updated = '1900-01-05T18:01:37Z'
        config.save()

    api = CanvasAPI(config.token, config.url)

    courses = [Course(x) for x in api.get_courses()]

    terms = set()
    for iclass in courses:
        terms.add(iclass.term)

    # Make class directories
    for term in terms:
        term_dir = os.path.join(config.directory, pathify(term))
        try:
            os.mkdir(term_dir)
        except (FileExistsError):
            pass

        for term_class in filter(lambda x: x.term == term, courses):
            course_dir = os.path.join(term_dir, pathify(term_class.name))
            try:
                term_class.directory = course_dir
                os.mkdir(course_dir)
                print(term_class.directory)
            except (FileExistsError):
                pass

    def create_folder(folder, directory, course):

        # Dump folder contents into class root if "course files"
        if not folder['name'] == "course files":
            folder_dir = directory + "/" + pathify(folder['name'])
            try:
                os.mkdir(folder_dir)
                print("Creating directory", folder_dir)
            except (FileExistsError):
                pass
        else:
            folder_dir = directory

        for file in filter(lambda x: x['folder_id'] == folder['id'], course.files):
            modified_at = dateutil.parser.parse(file['modified_at'])
            last_updated = dateutil.parser.parse(config.last_updated)
            if modified_at > last_updated:
                print("Downloading", file['filename'])
                r = requests.get(file['url'], stream=True)
                with open(folder_dir + '/' + pathify(file['filename']), 'wb') as opened_file:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            opened_file.write(chunk)


        child_folders = list(filter(lambda x: x['parent_folder_id'] == folder['id'], course.folders))

        if child_folders:
            for child_folder in child_folders:
                create_folder(child_folder, folder_dir, course)
        else:
            return

    for course in filter(lambda x: x.term == config.term, courses):
        course.folders = api.get_folders(course.id)
        course.files = api.get_files(course.id)
        root_folder = list(filter(lambda x: x['parent_folder_id'] == None, course.folders))[0]
        create_folder(root_folder, course.directory, course)

    config.last_updated = datetime.datetime.now(datetime.timezone.utc)
    config.save()


if __name__ == '__main__':
    main()
