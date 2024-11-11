#! /usr/bin/env python3

import os
import sys
import hashlib
import argparse
import json
import re
import xml.etree.ElementTree as ET
import zipfile
import shutil
import subprocess
import difflib

# append feature to record year ?
# append git or other CLI support
default_editor = 'vim'
default_repo = os.path.expanduser(r'~/workplace/paper-manage/repository/')
default_config_path = os.path.expanduser(r'~/.paper_manager')
default_obj_set = 'papers_repo.json'
default_config_file = '.config.xml'
default_xml_path = 'xml_repository'
if shutil.which('explorer.exe') :
    open_command = 'explorer.exe'
elif shutil.which('open') :
    open_command = 'open'
else :
    open_command = None

_file_obj_list = {}
VER = '1.8.3'
SN = 'Paper Manager (pm, pmanager)'
VER_MSG = '{} {}'.format(SN,VER)

def __merge_JSON(json_path) :
    print('Starting merging JSON record--')
    def name_chooser(s1,s2):
        check_sym = lambda a : len([c for c in a if c in '-_.()$1234567890'])
        return min(s1,s2,key=check_sym)
    def show(msg,text) :
        print('[MODIFY Mode]: {} {}'.format(arround_msg(MSG[msg]),text))
    MSG = {'title':'Title',
           'read':'Read Status'}
    msg_len = max([len(MSG[m]) for m in MSG])
    arround_msg = lambda s : '{} |-->'.format(s.ljust(msg_len))

    with open(json_path,'r') as fp :
        temp_dict = json.load(fp)
    conflict =False
    counter = 0
    for k in temp_dict :
        local_conflict = False
        counter += 1
        print('Merge [{}] in record ...'.format(k[:10]),end='')
        if k in _file_obj_list :
            s_obj = _file_obj_list[k]
            d_obj = temp_dict[k]
            set_keyword([s_obj],'keyword',d_obj['keyword'])
            set_keyword([s_obj],'author',d_obj['author'])
            if 'isRead' in d_obj :
                if not 'isRead' in s_obj :
                    set_read_status([s_obj],d_obj['isRead'])
                else :
                    if not s_obj['isRead'] == d_obj['isRead'] :
                        set_read_status([s_obj],'{}=>{}'.format(s_obj['isRead'],d_obj['isRead']))
                        conflict = True
                        local_conflict = True
                        print()
                        show('read',s_obj['isRead'])
                        set_keyword([s_obj],'keyword',['@*'])
            if not d_obj['name'] == s_obj['name']:
                if not local_conflict :
                    print()
                _name = name_chooser(s_obj['name'],d_obj['name'])
                conflict = True
                # bugs here, we should do, first new name, then set xml
                setName(s_obj,_name)
                show('title',_name)
                set_keyword([s_obj],'keyword',['@+-'])
        else :
            _file_obj_list[k] = temp_dict[k]
        print(' done. {}/{}'.format(counter,len(temp_dict)))
    __save_json()
    print('Merging JSON record complete.')
    return conflict

def __merge_xml(d_xml) :
    mapping = {'bib':'BibInformation',
               'review':'Review',
               'abs':'Abstract'}
    s_md5 = __xml_text_getter(d_xml,'FileInfo',mode='get',attr='md5')
    if __isFileMD5(s_md5) :
        pass
    else :
        return False
    obj = _file_obj_list[s_md5]
    s_path = obj['description']
    print('Merge [{}] \n   to [{}] ...'.format(d_xml,os.path.basename(s_path)),end='')
    if fileMD5(s_path) == fileMD5(d_xml) :
        print(' done.')
        return False
    else :
        print('MD5 checking fail')
        print('Conflict auto checking...')
    diff_text = lambda a : [s[2:] if s[0]==' ' else s for s in a]
    is_check = False
    for k in mapping :
        print('Checking difference with `{}`'.format(mapping[k]))
        text_merging = __xml_text_getter(d_xml,mapping[k])
        text_source = __xml_text_getter(s_path,mapping[k])
        if text_merging :
            if text_merging == 'None' :
                continue
            else :
                if text_source == 'None' :
                    __xml_text_setter(obj,mapping[k],text_merging)
                    continue
                else :
                    pass
        else :
            continue
        text_lst_s = text_source.splitlines(keepends=True)
        text_lst_s = [s+'\n' if not s[-1] == '\n' else s for s in text_lst_s]
        text_lst_d = text_merging.splitlines(keepends=True)
        text_lst_d = [s+'\n' if not s[-1] == '\n' else s for s in text_lst_d]
        diff_lst = difflib.ndiff(a,b)
        diff_count = len([1 for s in diff_lst if s[0] in '+-?'])
        if diff_count > 0 :
            is_check = True
        cmp_lst = diff_text(diff_lst)
        cmp_text = ''.join(cmp_lst)
        __xml_text_setter(obj,mapping[k],cmp_text)
    if is_check :
        set_keyword([obj],'keyword',['@+-'])
        print('  Merging process is done.')
    else :
        print('  Nothing should merge')
    return True

def __path_splitter(f_path) :
    f_sp_text = os.path.splitext(f_path)
    f_p = f_sp_text[0]
    f_ex = f_sp_text[1]
    f_n = os.path.basename(f_p)
    path_n = os.path.dirname(f_path)
    return path_n,f_n,f_ex

def __path_sorter(path_lst) :
    return sorted(path_lst,key=lambda a : len(os.path.basename(a)),reverse=True)

def __path_chooser(path_lst) :
    return max(path_lst,key=lambda a : len(os.path.basename(a)))

def __description_file_namer(pdf_path,has_md5=None) :
    r_path = os.path.expanduser(pdf_path)
    abs_path = os.path.abspath(r_path)
    path_n,f_n,f_ex = __path_splitter(pdf_path)
    if not f_ex == '.pdf' :
        return None
    if has_md5 :
        md5 = __isFileMD5(has_md5)
        if md5 :
            return _file_obj_list[md5]['description']
        else :
            f_n = md5[:6]
    else :
        f_n = fileMD5(abs_path)[:6]
    df_n = f_n+'_descript.xml'
    xml_path = os.path.join(default_config_path,default_xml_path)
    f_d_n = os.path.join(xml_path,df_n)
    return f_d_n

def __path_description_dir_checker(pdf_path) :
    check_path = __description_file_namer(pdf_path)
    if os.path.exists(check_path) :
        return True
    else :
        return False

def __compress_by_path_list(path_lst,arcname='',attr='',mode='w') :
    already = {}
    counter = 1
    processing_len = len(path_lst)
    processing_counter = 0
    if not len(path_lst) > 0 :
        return False
    default_zip_name = 'pmanager.zip'
    if attr :
        zip_name = '{}_{}'.format(attr,default_zip_name)
    else :
        zip_name = default_zip_name
    with zipfile.ZipFile(zip_name,mode,zipfile.ZIP_DEFLATED) as zf :
        for p in path_lst :
            processing_counter += 1
            if arcname :
                ps = arcname.upper()
            else :
                ps = 'Record File'
            print('\rCompressing... {} {}/{}'.format(ps,processing_counter,processing_len),end='')
            if os.path.exists(p) :
                if os.path.isfile(p) :
                    base_name = os.path.basename(p)
                    if not base_name in already :
                        pass
                    else :
                        code = fileMD5(p)[:6]
                        base_name = '_'.join([code,base_name])
                    already[base_name] = True
                    s_name = os.path.join(arcname,base_name)
                    zf.write(p,s_name)
                else :
                    print('FileError: {} is not a vaild file'.format(p))
            else :
                print('PathError: {} is not a vaild path'.format(p))
        print(' -> done.')
    return True

def __xml_indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            __xml_indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def __default_saving_path() :
    xml_path = os.path.join(default_config_path,default_xml_path)
    obj_path = os.path.join(default_config_path,default_obj_set)
    config_path = os.path.join(default_config_path,default_config_file)
    return xml_path, obj_path, config_path

def __mix_select(selected) :
    if type(selected) == list :
        sets = selected
    elif type(selected) == dict:
        sets = selected['index']+selected['key']
    else :
        print('TypeError: invaild type')

    mix_dict = {}
    for obj in sets :
        mix_dict[obj['md5']] = True
    mix_lst = [_file_obj_list[k] for k in mix_dict]
    return mix_lst

def __filter_of(data_lst,is_read=None,fixing=None,filter_key=None) :
    filter_lst = []
    if is_read :
        filter_lst = [obj for obj in data_lst if 'isRead' in obj]
        if is_read == 'reading' :
            filter_lst = [obj for obj in filter_lst if obj['isRead']=='reading']
    elif is_read == False :
        filter_lst = [obj for obj in data_lst if not 'isRead' in obj]
    else :
        filter_lst = data_lst

    if fixing :
        filter_lst = [obj for obj in filter_lst if len(obj['path']) == 0]

    # https://stackoverflow.com/questions/29687227/how-to-split-a-string-based-on-either-a-colon-or-a-hyphen
    if filter_key :
        find_of = lambda o : [k.lower() for k in o['keyword']+o['author']+re.split('[-:\s\.\_()]',o['name'])]
        for l in filter_key :
            filter_lst = [obj for obj in filter_lst if not l.lower() in find_of(obj)]
    return filter_lst

def __tag_spliter(k_list):
    tag_lst = []
    key_lst = []
    for k in k_list :
        if k[0] == '@' :
            tag_lst.append(k)
        else :
            key_lst.append(k)
    return key_lst,tag_lst

def __init_paper_manager() :
    if os.path.exists(default_config_path) :
        if os.path.isdir(default_config_path) :
            pass
        else :
            print('PathError: can not use default directory')
            os._exit(0)
    else :
        os.mkdir(default_config_path)

    xml_path, obj_path, config_path = __default_saving_path()

    if os.path.exists(config_path) :
        # method to read the config
        pass

    if os.path.exists(xml_path) :
        if os.path.isdir(xml_path) :
            pass
        else :
            print('PathError: can not use default xml directory')
            os._exit(0)
    else :
        os.mkdir(xml_path)

    if os.path.exists(obj_path) :
        # load the obj_path
        with open(obj_path,'r') as fp :
            global _file_obj_list
            _file_obj_list = json.load(fp)

def pdf_path_lister(dir_root=None) :
    if not dir_root :
        dir_root = default_repo
    for parents_name, dirs_name, files_name in os.walk(dir_root) :
        for file in files_name :
            if file.endswith('.pdf') :
                file_path = os.path.join(parents_name,file)
                yield file_path

def fileMD5(path) :
    with open(path,'rb') as f :
        md5 = hashlib.md5()
        md5.update(f.read())
        md5_code = md5.hexdigest()
    return md5_code

def __isFileMD5(code) :
    if not type(code) == str :
        return False
    if len(code) < 6 :
        return False
    for i in _file_obj_list :
        obj_md5 = _file_obj_list[i]['md5']
        if re.match(code,obj_md5):
            return obj_md5
    return False

def description_maker(pdf_path,paper_name=None,force=False,has_md5=None) :
    path_n,f_n,f_ex = __path_splitter(pdf_path)
    descrip_fn = __description_file_namer(pdf_path,has_md5=has_md5)
    if not descrip_fn :
        return None
    else :
        pass
    if os.path.exists(descrip_fn) and not force:
        return descrip_fn
    else :
        root = ET.Element('PaperInformation',Version='1.0')
        p_name = ET.SubElement(root,'PaperName')
        if paper_name :
            p_name.text = paper_name
        else :
            p_name.text = f_n
        if has_md5 :
            f_name = ET.SubElement(root,'FileInfo', md5=has_md5)
        else :
            f_name = ET.SubElement(root,'FileInfo', md5=fileMD5(pdf_path))
        #f_name.text = pdf_path
        key_word = ET.SubElement(root,'Keyword')
        key_word.text = 'None'
        key_word = ET.SubElement(root,'Author')
        key_word.text = 'None'
        bib_info = ET.SubElement(root,'BibInformation')
        bib_info.text = 'None'
        review_info = ET.SubElement(root,'Review')
        review_info.text = 'None'
        __xml_indent(root)
        full_tree = ET.ElementTree(root)
        full_tree.write(descrip_fn,xml_declaration=True,encoding='UTF-8',method='xml')
        return descrip_fn

def update_links ():
    # if lose xml link, check xml's md5 information to relink
    # or make a new xml
    need_fix = []
    print('[Update Mode]: Checking the vaild links...')
    for i in _file_obj_list :
        obj = _file_obj_list[i]
        if not os.path.exists(obj['description']) :
            print('[Relink Mode]: `{}` is not exist, try re-linking description xml'.format(obj['description']))
            d_path = __walk_xml(obj['md5'])
            if d_path :
                print('[Relink]: Find renamed xml file `{}`, and it is re-linked'.format(d_path))
                obj['description'] = d_path
            else :
                d_path = description_maker(obj['path'][0],obj['name'],True,obj['md5'])
                print('[Create Mode] : re-creating description xml {}'.format(d_path))
                obj['description'] = d_path
        temp_p = []
        loose_p = []
        for p in obj['path'] :
            if os.path.exists(p):
                temp_p.append(p)
            else :
                loose_p.append(p)
        obj['path'] = temp_p
        if loose_p :
            _msg = '[Remove invaild links]: '
            _l = len(_msg)
            print(_msg,end='')
            for _p in loose_p :
                print(p)
                print(' '*_l,end='')
            print()
        if temp_p :
            pass
        else :
            need_fix.append(obj['md5'])
            #print('Using `--fixlink {}` to add vaild link to file'.format(obj['md5']))
    if len(need_fix) > 0 :
        _msg = 'The file need to Fix: '
        _l = len(_msg)
        print(_msg)
        _count = 0
        for c in need_fix :
            print('>>',c)
            _count += 1
            if _count >= 10 :
                break
            #print(' '*_l,end='')
        if _count >= 10 :
            print('Currently shown 10/{} ...'.format(len(need_fix)))
            print('  Using `--select all --fixing` to show all record need to Fix')
        print()
        print('Using `--fixlink [md5 code] [<file name> | <dir>]` to add vaild link to file')
    else :
        print('All-update.')
    xml_path, obj_path, config_path = __default_saving_path()
    with open(obj_path,'w') as fp :
        json.dump(_file_obj_list,fp)
    return [_file_obj_list[k] for k in need_fix]

# input md5 
def __walk_xml(md5):
    md5 = __isFileMD5(md5)
    if md5 :
        pass
    else :
        return None
    xml_path, obj_path, config_path = __default_saving_path()
    for parents_name, dirs_name, files_name in os.walk(xml_path) :
        for file in files_name :
            if file.endswith('_descript.xml') :
                file_path = os.path.join(parents_name,file)
                temp_md5 = __xml_text_getter(file_path,'FileInfo',mode='get',attr='md5')
                if temp_md5 == md5 :
                    return file_path
    return None

def fixlink(md5,path,restore_mode=False) :
    _md5_r = __isFileMD5(md5)
    if _md5_r :
        pass
    else :
        print('FileError: `{}` is not MD5 code in record'.format(md5))
        os._exit(0)
    if restore_mode :
        candidate_path = {key:[] for key in _file_obj_list}
    else :
        if len(_file_obj_list[_md5_r]['path']) > 0 :
            print('The links of `{}` do not need to fix,\n'
                  '  using `--add` command to add file path to record'.format(_md5_r))
            os._exit(0)
    if os.path.exists(path) :
        if os.path.isdir(path) :
            for f_path in pdf_path_lister(path) :
                f_path = os.path.abspath(f_path)
                if restore_mode :
                    c_md5 = fileMD5(f_path)
                    if __isFileMD5(c_md5) :
                        candidate_path[c_md5].append(f_path)
                fixlink(md5,f_path,restore_mode)
            if restore_mode :
                return candidate_path
        else :
            if _md5_r == fileMD5(path) :
                _file_obj_list[_md5_r]['path'].append(path)
                if not restore_mode :
                    o = _file_obj_list[_md5_r]
                    print('[Re-link Mode]')
                    print('[{}]: --> {}'.format(o['md5'][:6],'.../'+os.path.basename(__path_chooser(o['path']))))
                    __save_json()
                    os._exit(0)
    else :
        print('PathError: `{}` is not a vaild path'.format(path))
        os._exit(0)

def rename_xml(f_md5,new_name) :
    pass

def pdf_object_maker(pdf_path) :
    if os.path.exists(pdf_path) :
        pass
    else :
        return None
    temp = {}
    temp['name'] = pdf_path.split('/')[-1]
    temp['path'] = [pdf_path]
    temp['md5'] = fileMD5(pdf_path)
    temp['author'] = []
    temp['keyword'] = []
    if __path_description_dir_checker(pdf_path) :
        temp['description'] = __description_file_namer(pdf_path)
    else :
        temp['description'] = ''
    return temp

def add_into_tracking(pdf_path,name=None,force=False) :
    r_path = os.path.expanduser(pdf_path)
    abs_path = os.path.abspath(r_path)
    global _file_obj_list
    if os.path.exists(r_path) :
        pass
    else :
        return False
    if os.path.isdir(r_path) :
        for f_path in pdf_path_lister(r_path) :
            add_into_tracking(f_path)
    else :
        f_md5 = fileMD5(pdf_path)
        if f_md5 in _file_obj_list :
            if not abs_path in  _file_obj_list[f_md5]['path'] :
                _file_obj_list[f_md5]['path'].append(abs_path)
        else :
            descri_path = description_maker(pdf_path,force)
            print('[Create Mode] : {}'.format(descri_path))
            pdf_obj = pdf_object_maker(abs_path)
            _file_obj_list[f_md5] = pdf_obj
            print('[{}] -> {}'.format(f_md5,abs_path))
    xml_path, obj_path, config_path = __default_saving_path()
    with open(obj_path,'w') as fp :
        json.dump(_file_obj_list,fp)
        return True

def __show_detail(obj,len_lst,rank=5):
    k_lst,t_lst = __show_simplify(obj)
    md5_str = 'Tracking on path --> '
    if len_lst <= rank :
        _show_path_lst = obj['path']
    else :
        _show_path_lst = [__path_chooser(obj['path'])]
    if len_lst <= rank :
        print('[XML Describer]: {}'.format(os.path.basename(obj['description'])))
    print(md5_str,end='')
    for s in obj['path'] :
        print(s,end='')
        if len_lst <= rank :
            print('\n'+' '*len(md5_str),end='')
        else :
            if len(obj['path']) > 1 :
                print('  (1/{} path is listed)'.format(len(obj['path'])))
            print()
            break
    if not obj['path'] :
        print()
    return k_lst,t_lst

def __show_simplify(obj):
    def show(msg,text) :
        print('{}: {}'.format(arround_msg(MSG[msg]),text))
    MSG = {'title':'Title',
           'author':'Author',
           'tag':'Tags',
           'read':'Read Status',
           'md5':'Hash Code',
           'keyword':'Keyword'}
    msg_len = max([len(MSG[m]) for m in MSG])
    arround_msg = lambda s : '[{}]'.format(s.center(msg_len))
    k_lst,t_lst = __tag_spliter(obj['keyword'])
    print()
    show('title',obj['name'])
    show('md5',obj['md5'][:10])
    if t_lst :
        show('tag',', '.join(t_lst))
    if k_lst :
        show('keyword',', '.join(k_lst))
    if obj['author']:
        show('author',', '.join(obj['author']))
    if 'isRead' in obj :
        show('read',obj['isRead'])
    return k_lst,t_lst

def showObjs(obj_list=None,detail=False) :
    if obj_list :
        if type(obj_list) == dict :
            _obj_list = __mix_select(obj_list)
            len_lst = len(_obj_list)
        else :
            _obj_list = obj_list
            len_lst = len(_obj_list)
    else :
        _obj_list = [_file_obj_list[i] for i in _file_obj_list]
        len_lst = len(_file_obj_list)
    islist = {}
    allTags = {}
    for i in _obj_list :
        if type(_obj_list) == list :
            obj = i
        else :
            print('Error: Type Error')
            os._exit(0)
        if obj['md5'] in islist :
            continue
        else :
            islist[obj['md5']] = True
        if detail :
            k_lst,t_lst = __show_detail(obj,len(_obj_list))
        else :
            k_lst,t_lst = __show_simplify(obj)
        if not obj['path'] :
            print('  [FIXING MSG]: The {} lost the link,\n'
                  '    Using `--fixlink {} [<file name> | <dir>]` to re-link'.format(obj['md5'][:6],obj['md5'][:6]))
        for t in t_lst :
            if t in allTags :
                pass
            else :
                allTags[t] = True
    print('\n{} record in tracking is selected.'.format(len(_obj_list)))
    if allTags :
        print('  [TAGs IN SELECT]: {}'.format(', '.join([t for t in allTags])))

def restore(target_path) :
    # based on xml and json, update the full repo in new repo (witch export by this program)
    # how to compare update for xml ?
    if os.path.exists(target_path):
        if os.path.isdir(target_path):
            pass
        else :
            print('RestoreError: Cannot use file to restore data')
            os._exit(0)
    else :
        print('PathError: Path is not exists')
        os._exit(0)
    candidate_path = None
    fix_obj = update_links()
    if len(fix_obj) == 0:
        os._exit(0)
    else :
        print()
    print('[Restore Mode]: Try to recover link with {}'.format(target_path))
    counter = 0
    len_lst = len(fix_obj)
    for obj in fix_obj :
        if candidate_path :
            obj['path'] = candidate_path[obj['md5']]
        else :
            candidate_path = fixlink(obj['md5'],target_path,True)
    re_obj = [o for o in fix_obj if o['path']]
    for o in re_obj :
        print('[{}]: --> {}'.format(o['md5'][:6],'.../'+os.path.basename(__path_chooser(o['path']))))
    print('{}/{} files is recover.'.format(len(re_obj),len(fix_obj)))
    __save_json()
    return True

def check_file(file_path) :
    if os.path.exists(file_path) :
        if os.path.isfile(file_path) :
            c_md5 = fileMD5(file_path)
            if c_md5 in _file_obj_list :
                obj = _file_obj_list[c_md5]
                showObjs([obj],True)
                if not os.path.abspath(file_path) in obj['path'] :
                    print('\n[CHECK MSG]: This file is not tracking,\n  using command `--add {}` to track it'.format(file_path))
            else :
                    print('\n[CHECK MSG]: This file is not exist,\n  using command `--add {}` to track it'.format(file_path))

def select_obj(para,detail=False,inner=False) :
    return_arg = ['all','key','index']
    def iskey(obj_i,key_para) :
        if key_para :
            if not 'keyword' in obj_i :
                obj_i['keyword'] = []
            if not 'author' in obj_i :
                obj_i['author'] = []
            find_of = obj_i['keyword']+obj_i['author']+re.split('[-:\s\.\_()]',obj_i['name'])
            find_of = [k.lower() for k in find_of if k]
            if inner :
                test_lst = [k for k in key_para if not k in find_of]
                if not test_lst :
                    return True
                elif len(test_lst) == 1 and '@' in test_lst :
                    _t = [k for k in find_of if k[0] == '@']
                    if _t :
                        return True
                    else :
                        return False
                else :
                    return False
            for k in find_of :
                if k in key_para :
                    return True
                if '@' in key_para :
                    if k[0] == '@' :
                        return True
            return False
        else :
            return False

    # check is path
    def ispath(para_i) :
        if os.path.exists(para_i):
            if os.path.isfile(para_i) :
                c_md5 = fileMD5(para_i)
                check_code = __isFileMD5(c_md5)
                if check_code :
                    return _file_obj_list[check_code]
                else :
                    return False
            else :
                return False
        else :
            return False

    # check is md5
    def ismd5(para_i):
        check_code = __isFileMD5(para_i)
        if check_code :
            return _file_obj_list[check_code]
        else:
            return False

    if para[0] == 'all' and not inner:
        return [_file_obj_list[k] for k in _file_obj_list]

    key_para = []
    temp = {'index':[],'key':[]}
    for para_i in para :
        _get_item = ismd5(para_i)
        if _get_item :
            if not _get_item in temp['index'] :
                temp['index'].append(_get_item)
            continue
        _get_item = ispath(para_i)
        if _get_item :
            if not _get_item in temp['index'] :
                temp['index'].append(_get_item)
            continue
        key_para.append(para_i.lower())

    # candidate targets
    if detail :
        counter = 0
    for i in _file_obj_list :
        if detail :
            counter+=1
            print('\rProcessing: {}/{}'.format(counter,len(_file_obj_list)),end='',flush=True)
        obj = _file_obj_list[i]
        if iskey(obj,key_para) :
            temp['key'].append(obj)
    if detail :
        print()
    return temp

def setName(obj,new_name) :
    if not obj :
        return False
    if new_name :
        pass
    else :
        return False
    xml_path = obj['description']
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for n in root.iter('PaperName') :
        n.text = new_name
        break
    __xml_indent(root)
    tree = ET.ElementTree(root)
    tree.write(xml_path,xml_declaration=True,encoding='UTF-8',method='xml')
    obj['name'] = new_name
    xml_path, obj_path, config_path = __default_saving_path()
    with open(obj_path,'w') as fp :
        json.dump(_file_obj_list,fp)
    return True

def __save_json() :
    xml_path, obj_path, config_path = __default_saving_path()
    with open(obj_path,'w') as fp :
        json.dump(_file_obj_list,fp)

def __xml_text_setter(obj,target,text='None') :
    type_mapping = {'bib':'BibInformation',
                    'abs':'Abstract',
                    'keyword':'Keyword',
                    'author':'Author',
                    'review':'Review'}
    type_usable = [type_mapping[i] for i in type_mapping]
    if target in type_mapping :
        target = type_mapping[target]
    elif target in type_usable :
        pass
    else :
        return None
    break_flag = True
    xml_path = obj['description']
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for n in root.iter(target) :
        n.text = text.strip()
        break_flag = False
        break
    if break_flag :
        temp = ET.SubElement(root,target)
        temp.text = text.strip()
    __xml_indent(root)
    tree = ET.ElementTree(root)
    tree.write(xml_path,xml_declaration=True,encoding='UTF-8',method='xml')

def __xml_text_getter(obj,target,mode='text',attr='name') :
    if mode in ['text','get'] :
        pass
    else :
        return ''
    if type(obj) == str :
        xml_path = obj
    elif type(obj) == dict :
        xml_path = obj['description']
    else :
        return ''
    tree = ET.parse(xml_path)
    root = tree.getroot()
    for n in root.iter(target) :
        if mode == 'get' :
            return n.get(attr)
        if mode == 'text' :
            if n.text :
                return n.text.strip()
            else :
                return 'None'
    return ''

# should add absract?
def __markdown_templete(obj,review_text,based_rank=1,get_abs=False):
    rank_mark = '#'
    title = '{} {}\n\n'.format(rank_mark*based_rank,obj['name'])
    author = '**Author:** {}\n\n'.format(', '.join(obj['author']))
    if review_text :
        review = '{} {}\n\n {}\n\n'.format(rank_mark*(based_rank+1),'Review Content',review_text)
    else :
        review = ''
    if get_abs :
        paper_abs = __xml_text_getter(obj,'Abstract')
        if paper_abs :
            paper_abs = '{} {}\n\n {}\n\n'.format(rank_mark*(based_rank+1),'Abstract',paper_abs)
    else :
        paper_abs = ''
    return title+author+paper_abs+review

def __sub_editor(file_name,editor_name) :
    if type(file_name) == str :
        pass
    else :
        return False
    command = ' '.join([editor_name,file_name])
    sp = subprocess.Popen(command,shell=True)
    sp.wait()
    if sp.poll() == 0 :
        return True
    else :
        return False

def __para_checker(para,para_len='*') :
    if len(para) > 0 :
        return True
    else :
        print('SelectedError: can not operate with nothing')
        return False

def write_by_editor(obj,set_type):
    if shutil.which(default_editor) :
        pass
    else :
        print('CommandError: Default editor {} is not exists.')
        os._exit(0)
    temp_file = '.INFO_EDITING.md'
    temp_path = os.path.join(default_config_path,temp_file)
    type_mapping = {'bib':'BibInformation',
                    'abs':'Abstract',
                    'abstract':'Abstract',
                    'review':'Review'}
    if not set_type in type_mapping :
        print('ParameterError: `{}` is invaild.'.format(set_type))
        os._exit(0)
    text = __xml_text_getter(obj,type_mapping[set_type])
    with open(temp_path,'w') as fp :
        fp.write(text)
    if __sub_editor(temp_path,default_editor) :
        print('Writing... ',end='')
        with open(temp_path,'r') as fp :
            text = fp.read()
            print('total {} words.'.format(len(text)))
            __xml_text_setter(obj,type_mapping[set_type],text)
        print('[Write Mode]: The edited text is saved.')
        return True
    else :
        print('UnknowError: editor faults with unknow reason')
        return False

def import_xml_content(target_obj,set_type,in_path,mode='add'):
    type_mapping = {'bib':'BibInformation',
                    'abs':'Abstract',
                    'abstract':'Abstract',
                    'review':'Review'}
    if not set_type in type_mapping :
        print('ParameterError: `{}` is invaild.'.format(set_type))
        os._exit(0)
    if os.path.exists(in_path) :
        if os.path.isfile(in_path) :
            with open(in_path,'r') as fp :
                text = fp.read().strip()
                if mode == 'add' and set_type == 'review':
                    text += '\n\n{}'.format(__xml_text_getter(target_obj,type_mapping[set_type]))
                __xml_text_setter(target_obj,type_mapping[set_type],text.strip())
        else :
            print('PathError: `{}` is not a file'.format(in_path))
            os._exit(0)
    else :
        print('PathError: `{}` is not a vaild path'.format(in_path))
        os._exit(0)
    pass

def set_keyword(sele_lst,set_type,keyword_lst,mode='add',split_by=''):
    if __para_checker(sele_lst) :
        pass
    else :
        os._exit(0)
    default_mode = ['add','set','rm']
    mapping = {'keyword':'Keyword',
               'author':'Author'}
    if not mode in default_mode :
        print('ParameterError: `{}` is invaild.'.format(mode))
        os._exit(0)
    if not set_type in mapping :
        print('ParameterError: `{}` is invaild.'.format(set_type))
        os._exit(0)
    if split_by :
        keyword_lst = ' '.join(keyword_lst).split(split_by)
        keyword_lst = [s.strip() for s in keyword_lst]
    for obj in sele_lst :
        if mode == 'add' :
            if not set_type in obj :
                obj[set_type] = []
            for k in keyword_lst :
                if not k in obj[set_type] :
                    obj[set_type].append(k)
        elif mode == 'rm' :
            obj[set_type] = [k for k in obj[set_type] if not k in keyword_lst]
        else :
            obj[set_type] = keyword_lst
        if set_type == 'keyword' :
            just_key_word = [key for key in obj[set_type] if not '@' in key]
        else :
            just_key_word = obj[set_type]
        __xml_text_setter(obj,mapping[set_type],', '.join(just_key_word))
    xml_path, obj_path, config_path = __default_saving_path()
    with open(obj_path,'w') as fp :
        json.dump(_file_obj_list,fp)

def set_read_status(sele_lst,status,mode='add') :
    if __para_checker(sele_lst) :
        pass
    else :
        os._exit(0)
    set_mode = ['add','set','rm','del']
    if not mode in set_mode :
        print('ParameterError: Fault choosen mode')
        os._exit(0)
    if mode in ['add','set'] :
        for obj in sele_lst :
            obj['isRead'] = status
    else :
        for obj in sele_lst :
            if 'isRead' in obj :
                obj.pop('isRead')
    __save_json()

def cat_from_xml(sele_lst,trg_type) :
    usable_type = ['bib','review','abs','abstract']
    type_mapping = {'bib':'BibInformation',
                    'review':'Review',
                    'abs':'Abstract',
                    'abstract':'Abstract'}
    if not trg_type in usable_type :
        print('ParameterError: Type `{}` is not vaild'.format(trg_type))
        os._exit(0)
    for obj in sele_lst :
        text = __xml_text_getter(obj,type_mapping[trg_type])
        print()
        print(text)

def export_file(sele_lst,export_type,mode='add') :
    xml_path, obj_path, config_path = __default_saving_path()
    # will add 'review', 'markdown(md)', 'bib'
    usable_type = ['xml','stash','backup','backup-all','pdf','bib','review','abs','abstract','markdown','md','blank']
    type_mapping = {'bib':'BibInformation',
                    'review':'Review',
                    'abs':'Abstract',
                    'abstract':'Abstract'}
    mode_map = {'set':'w','add':'a'}
    if not export_type in usable_type :
        print('ParameterError: Type `{}` is not vaild'.format(export_type))
        os._exit(0)
    if export_type == 'xml' :
        p_lst = [obj['description'] for obj in sele_lst]
        __compress_by_path_list(p_lst,'xml',export_type)
    elif export_type == 'stash' :
        shutil.copy(obj_path,os.path.basename(obj_path))
    elif export_type == 'pdf' :
        p_lst = [obj['path'][0] for obj in sele_lst]
        if len(p_lst) > 1 :
            __compress_by_path_list(p_lst,'pdf',export_type)
        else :
            shutil.copy(p_lst[0],os.path.basename(p_lst[0]))
    elif export_type == 'backup' :
        # need to add config when it has config
        p_lst = [obj['description'] for obj in sele_lst]
        __compress_by_path_list(p_lst,default_xml_path,export_type)
        __compress_by_path_list([obj_path],'',export_type,'a')
    elif export_type == 'backup-all' :
        # need to add config when it has config
        xml_lst = [obj['description'] for obj in sele_lst]
        pdf_lst = [__path_chooser(obj['path']) for obj in sele_lst]
        __compress_by_path_list(pdf_lst,'pdf',export_type)
        __compress_by_path_list(xml_lst,default_xml_path,export_type,'a')
        __compress_by_path_list([obj_path],'',export_type,'a')
    elif export_type == 'bib' :
        text_lst = []
        p_lst = [obj['description'] for obj in sele_lst]
        for p in p_lst :
            text_lst.append(__xml_text_getter(p,type_mapping[export_type]))
        text = '\n\n'.join(text_lst)
        with open('pmanager_auto_bib.bib',mode_map[mode]) as fp:
            fp.write(text)
    elif export_type == 'blank' :
        for obj in sele_lst :
            with open('{}_auto_create.md'.format(obj['md5'][:6]),mode_map[mode]) as fp:
                pass
    elif export_type == 'review' :
        with open('pmanager_auto_markdown.md',mode_map[mode]) as fp:
            for obj in sele_lst :
                get_text = __xml_text_getter(obj,type_mapping[export_type])
                _text = __markdown_templete(obj,get_text)
                fp.write(_text)
    elif export_type in ['abs','abstract'] :
        with open('pmanager_auto_markdown.md',mode_map[mode]) as fp:
            for obj in sele_lst :
                _text = __markdown_templete(obj,None,get_abs=True)
                fp.write(_text)
    elif export_type in ['markdown','md'] :
        with open('pmanager_auto_markdown.md',mode_map[mode]) as fp:
            for obj in sele_lst :
                get_text = __xml_text_getter(obj,type_mapping['review'])
                _text = __markdown_templete(obj,get_text,get_abs=True)
                fp.write(_text)
    else :
        print('SupportError: The Type {} do not support yet'.format(export_type))
    os._exit(0)

# 改成資料夾的話先merge json update後 然後才merge xml
def merging(mpath) :
    is_target = lambda a : True if a == default_obj_set or a.endswith('_descript.xml') else False
    def get_lst() :
        for parents_name, dirs_name, files_name in os.walk(mpath) :
            for file in files_name :
                if is_target(file) :
                    file_path = os.path.join(parents_name,file)
                    yield file_path

    if os.path.exists(mpath) :
        pass
    else :
        print('PathError: the path `{}` is invaild'.format(mpath))
        os._exit(0)
    is_conflict = False
    if os.path.isfile(mpath) :
        if is_target(os.path.basename(mpath)) :
            if mpath.endswith('.json') :
                is_conflict = __merge_JSON(mpath)
                update_links()
            else :
                is_conflict = __merge_xml(mpath)
        else :
            print('TargetError: Target File is not vaild to merge')
            os._exit(0)
    elif os.path.isdir(mpath) :
        print('Get merging object ... ',end='')
        files_lst = [p for p in get_lst()]
        print('done')
        print('Finding record JSON File... ',end='')
        xml_lst = []
        for p in files_lst :
            if p.endswith('.json') :
                print()
                is_conflict = __merge_JSON(p)
            else :
                xml_lst.append(p)
        print('Done.')
        files_lst = xml_lst
        fix_lst = update_links()
        files_len = len(files_lst)
        files_counter = 0
        for p in files_lst :
            files_counter += 1
            print('Merge the target {}/{}'.format(files_counter,files_len))
            is_conflict = __merge_xml(p)
    else :
        print('TargetError: Target Path is not vaild to merge')
        os._exit(0)
    if fix_lst :
        print('\nUsing `--restore <dir>` to recover un-link record')
    if is_conflict :
        print('\nUsing `--select @*` to check the conflict record')
        print('  Checked the conflict is solved,'
              '  use `--select <md5> --mode rm -k @*` to remove conflict tag')

def remove_tracking(remove_lst,is_force=False):
    if type(remove_lst) == list:
        pass
    else :
        print('TypeError: Removing target cannot be {}'.format(type(remove_lst)))
        os._exit(0)
    print('Remove processing ...')
    is_removed_lst = []
    for p in remove_lst :
        if os.path.exists(p) :
            if os.path.isfile(p) :
                print('Checking `{}` in the tracking ... '.format(p),end='')
                _md5 = __isFileMD5(fileMD5(p))
                if _md5 :
                    print(' done.')
                    obj = _file_obj_list[_md5]
                    showObjs([obj],True)
                    if not is_force :
                        check = input('Remove Tracking ? (Y/n) ')
                        if check in 'Yy' :
                            pass
                        else :
                            print('Passing...')
                            continue
                    print('Removing [{} ... {}] tracking'.format(_md5[:6],_md5[-6:]))
                    is_removed_lst.append([_file_obj_list.pop(_md5),p])
                else :
                    print(' failed')
                    print('  `{}` do not exists in tracking'.format(p))
                    print('  Using `--add {}` to track the file'.format(p))
                    continue
            else :
                print('TargetError: {} is not a file'.format(p))
                continue
        else :
            print('TargetError: {} is not a vaild path'.format(p))
            continue
    if is_removed_lst :
        print('\nFollowing tracking items are removed:')
        for r in is_removed_lst :
            print()
            print('     Title: {}'.format(r[0]['name']))
            print('   Keyword: {}'.format(', '.join(r[0]['keyword'])))
            print('    Author: {}'.format(', '.join(r[0]['author'])))
            print('XML record: {}'.format(os.path.basename(r[0]['description'])))
            print('    Re-add: {}'.format('--add {}'.format(r[1])))
        print('\nNote: XML records would not remove directly.\n  They still can be found at `~/.paper_manager/xml_repository`')
        __save_json()
    else :
        print('\nNothing is removed')
        os._exit(0)

def check_unused_xml():
    xml_path, obj_path, config_path = __default_saving_path()
    def xml_iter() :
        for parents_name, dirs_name, files_name in os.walk(xml_path) :
            for file in files_name :
                if file.endswith('.xml') :
                    file_path = os.path.join(parents_name,file)
                    yield file_path
    xmls = [os.path.basename(p) for p in xml_iter()]
    used_xmls = [os.path.basename(_file_obj_list[k]['description']) for k in _file_obj_list]
    unused_lst = []
    for p in xmls :
        if p in used_xmls :
            pass
        else :
            unused_lst.append(p)
    if unused_lst :
        print('Following XML file is unused:')
        for p in unused_lst :
            print('>> {}'.format(p))
        print('\nFind files in {}'.format(xml_path))
    else :
        print('\nNothing is unused.')

if __name__ == '__main__' :
    __init_paper_manager()
    if len(sys.argv) == 1 :
        print(VER_MSG)
        print('Please using command `-h` or `--help` to get help,\n  or using `-v` or `--version` to get version information')
        os._exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument('-v','--version', action='version', version=VER_MSG)
    parser.add_argument('-a','--add',help='add target PDF file (under directory) into tracking')
    parser.add_argument('-l','--list',action='store_true',help='list the tracking file information')
    parser.add_argument('--clear',action='store_true',help='Inspect XML file is not used')
    parser.add_argument('--check',help='check the file whether it is tracked')
    parser.add_argument('--remove',nargs='+',help='Input designated paths to remove')
    parser.add_argument('--update',action='store_true',help='check the link of each tracking item whether it is exists')
    parser.add_argument('--restore',help='based on target directory to re-build tracking item and PDF file relationship')
    parser.add_argument('--merge',help='merge the modify from other way')
    parser.add_argument('--select',nargs='+',help='select the tracking item by `all`, keyword, name (title), author, or using md5/path of file precisely')
    parser.add_argument('--name',nargs='+',help='set the title name for designated single file')
    parser.add_argument('-k','--keyword',nargs='+',help='set the keyword for selected files, using `@` header can set keyword as tag')
    parser.add_argument('--author',nargs='+',help='set the authors of selected files')
    parser.add_argument('--read',help='set the reading status of tracking item')
    parser.add_argument('--write',help='Open the default editor `{}` to edit the `abstract (abs)`, `bib`, `review` for selected item'.format(default_editor))
    parser.add_argument('--get_in',nargs=2,help='import the `abstract (abs)`, `bib`, `review` information of designated item from a text file')
    parser.add_argument('--fixlink',nargs=2,help='fix the lost file link of designated item from the directory')
    parser.add_argument('--print',help='Print the `bib`, `abs`, or `review`')
    parser.add_argument('--export',help='export the `bib`, `markdown`, `pdf` and `backup` of tracking files')
    parser.add_argument('--open',action='store_true',help='using default program to open tracking pdf file')
    parser.add_argument('--opendir',action='store_true',help='using default program to open directory of tracking pdf file')
    parser.add_argument('--mode',default='add',help='mode of add/set/rm for set (keywod/author), import (review), export (markdown/bib)')
    parser.add_argument('-f','--force',action='store_true',help='force to create new xml record file')
    parser.add_argument('--inner',action='store_true',help='change `--select` operation into inner join')
    parser.add_argument('--detail',action='store_true',help='Print out detail message for `--select` and `--list`')
    parser.add_argument('--fixing',action='store_true',help='filter parameter, filter form original selected items, which is need to fix (no file link)')
    parser.add_argument('--is_read',action='store_true',help='filter parameter, filter form original selected items, which is read')
    parser.add_argument('--reading',action='store_true',help='filter parameter, filter form original selected items, which is reading')
    parser.add_argument('--not_read',action='store_true',help='filter parameter, filter form       original selected items, which is not read')
    parser.add_argument('--filters',nargs='+',help='Filter the seleted result by arguments')
    args = parser.parse_args()
    if args.list :
        showObjs(detail=args.detail)
        os._exit(0)
    if args.add :
        if args.add == '/' :
            print('PathError: root cannot be target')
        else :
            add_into_tracking(args.add,args.name,args.force)
        os._exit(0)
    if args.remove :
        remove_tracking(args.remove,args.force)
        os._exit(0)
    if args.update :
        update_links()
        os._exit(0)
    if args.clear :
        check_unused_xml()
        os._exit(0)
    if args.fixlink :
        _md5_f, _path_f = args.fixlink
        fixlink(_md5_f, _path_f)
        os._exit(0)
    if args.check :
        check_file(args.check)
        os._exit(0)
    if args.restore :
        restore(args.restore)
        os._exit(0)
    if args.merge :
        merging(args.merge)
        os._exit(0)

    if args.select :
        selected = select_obj(args.select,inner=args.inner)
        if args.is_read or args.not_read or args.reading or args.fixing or args.filters:
            read_flag = None
            if args.is_read and args.not_read and args.reading:
                print('ParameterError: `is_read`, `not_read` and `reading` is conflict')
                os._exit(0)
            else :
                if args.not_read :
                    read_flag = False
                elif args.is_read :
                    read_flag = True
                elif args.reading :
                    read_flag = 'reading'
                else :
                    pass
            if 'key' in selected and 'index' in selected :
                selected['key'] = __filter_of(selected['key'],read_flag,args.fixing,args.filters)
                selected['index'] = __filter_of(selected['index'],read_flag,args.fixing,args.filters)
            else :
                selected = __filter_of(selected,read_flag,args.fixing,args.filters)
        if args.export :
            export_command = ['pdf','bib','abstract','review','backup','backup-all','stash','xml','abs','markdown','md','blank']
            if args.export in export_command :
                targets = __mix_select(selected)
                export_file(targets,args.export,args.mode)
            else :
                print('ParameterError: Type `{}` is not vaild'.format(args.export))
                os._exit(0)
        elif args.print :
            export_command = ['bib','review','abs','abstract']
            if args.print in export_command :
                targets = __mix_select(selected)
                cat_from_xml(targets,args.print)
            else :
                print('ParameterError: Type `{}` is not vaild'.format(args.print))
        elif args.write :
            if selected :
                targets = selected['index']
                if len(targets) == 1 :
                    write_by_editor(targets[0],args.write)
                elif len(selected) > 1 :
                    print('TargetError: Too many target')
                else :
                    print('TargetError: Nothing can be set ')
        elif args.get_in :
            in_type,in_path = args.get_in
            if selected :
                targets = selected['index']
                if len(targets) == 1 :
                    import_xml_content(targets[0],in_type,in_path,args.mode)
                elif len(selected) > 1 :
                    print('TargetError: Too many target')
                else :
                    print('TargetError: Nothing can be set ')
        elif args.name :
            # maybe should change metric
            if selected :
                targets = selected['index']
                if len(targets) == 1 :
                    n_name = ' '.join(args.name)
                    setName(targets[0],n_name)
                elif len(selected) > 1 :
                    print('SetNameError: Too many target')
                else :
                    print('SetNameError: Nothing to set name')
        elif args.open or args.opendir:
            if selected :
                if not open_command :
                    print('CommandError: System do not support command `--open` currently.')
                targets = selected['index']
                if len(targets) == 1 :
                    _path = targets[0]['path'][0]
                    _dir_path = os.path.dirname(_path)
                    if args.open :
                        _command = ' '.join([open_command,_path])
                        os.system(_command)
                    if args.opendir :
                        _command = ' '.join([open_command,_dir_path])
                        os.system(_command)
                    os._exit(0)
                elif len(selected) > 1 :
                    print('SetNameError: Too many target')
                else :
                    print('SetNameError: Nothing to set name')
        elif args.keyword :
            if selected :
                targets = __mix_select(selected)
                set_keyword(targets,'keyword',args.keyword,args.mode)
        elif args.author :
            if selected :
                targets = __mix_select(selected)
                set_keyword(targets,'author',args.author,args.mode,',')
        elif args.read :
            if selected :
                targets = __mix_select(selected)
                set_read_status(targets,args.read,args.mode)
        else :
            # maybe should print
            if selected :
                showObjs(selected,args.detail)
            else :
                print('Nothing can be selected')
    else :
        if args.export :
            export_command = ['stash']
            if args.export in export_command :
                export_file([],args.export)
            else :
                print('ParameterError: Other type should use after select')
                os._exit(0)

