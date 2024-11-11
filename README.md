# Paper Manager Public version (v1.8.2)

The centralized command line tool for distributed literatures management.

Reference to the command design of  git and SQL, the command design is close to natural language.

The information storing is depending on the md5 code of file, and support record distributed file with same md5 code.

**Update in v1.8.2(0220)**:
1. fix the bug can not use `@`

**Update in v1.8.2**:
1. feature `--write` will show the number of writing words.
2. Now `--select` can parse the word near `:` and `()`.
3. New `--reading` can filter the tracking record which read status is "reading".

**Update in v1.8.1**: 
1. `--remove` feature is done, which can remove tracking on JSON record
2. `--clear` feature is done, which can find the xml file do not in tracking

**Update in v1.8**: 
1. Add `--merge` feature, but do not suggest
2. Simplify `--update` print out
3. Fix the undefined operation in same file name scenes
4. Beautify compressing process
5. Modify name logic for xml files
6. Modify logic of description_file_namer to support above modify

**Update in v1.7**: 
1. `--write` feature is done, which can modify `review`, `bib` and `abstract`(`abs`) by default editor, instead of `--get_in`.
2. Now, if selected results is nothing, it will print out the error message
3. Fix the bug of cannot print out the read status message.

**Update in v1.6**: 
1. More clearly format for detail message
2. `--filters` feature is done
3. Now, the record need to fix will print out message in `--list` and `--select`
4. More clearly MSG for re-link process

**Update in v1.5.1**: 
1. More readable, simple and beautiful print out result.
2. Now can use `--export blank` to export selected items blank markdown file which has md5 in file name.

**Update in v1.5**: 
1. In v1.5 version, optimize the print out format, now more clearly and concise.
2. Now, it can open the designated pdf file and its directory by `--open` and `--opendir`. 
3. More powerful, useful and clearly Tag function
4. More efficient restore command
5. The intersection search i.e., inner join selecting


## Content

* [Intro](#intro)
* [Usage](#usage)
  * [Basic Features](#basic-features)
    * [Add into tracking](#add-into-tracking)
    * [List the tracking information](#list-the-tracking-information)
    * [Set Title and Keyword](#set-title-and-keyword)
    * [Get specific file tracked status](#get-specific-file-tracked-status)
  * [Advance Feature](#advance-feature)
    * [Import information from file](#import-information-from-file)
    * [Export information by designated format](#export-information-by-designated-format)
    * [Action mode](#action-mode)
    * [Tag](#tag)
    * [Selection of Inner-Join](#selection-of-inner-join)
    * [Filter](#filter)
  * [Storing Architecture](#storing-architecture)
    * [Update and restore](#update-and-restore)
    * [Backup and git](#backup-and-git)
  * [Other Command Support](#other-command-support)

## Intro

The management tool for distributed pdf literatures, which provide following feature:
* Tracking the file by MD5 hash code
    * Record the literatures content and the pdf path relation
    * Maintain the tracking record and file path relation by CLI command
    * Fix related link after change path or backup-restore in one command
    * Inspect whether the file is tracking and view tracking status by hash code or file path
    * Support one command open the designated file and its directory
    * Support PDF File and record backup by command
* Support the reading progress and BibTeX bibliography management
    * Add the reading status into record
    * Add the reading review into tracking
    * Add the paper abstract into storing
    * Export multiple BibTeX record into a single BibTeX `.bib` file
    * Export multiple review and abstract record into a single file
* The useful Selection and Operation designment
    * Intuitive command designment
    * support union selecting record item 
    * support intersection selecting record item
    * support the simple filter, enforce on selected results 
    * search record item by keyword, author, title, and Tag.

## Usage

In following description we will set the main program `paper_manager.py` to `paper_manager`.

**Note**: This program will create the necessary directory for record file under path `~/.paper_manager`.

### Basic Features

#### Add into tracking

Add the target paper or the papers under target directory into tracking.

```bash
paper_manager --add [file | dir]
```

If the file is not recorded, it will print out MD5 file check code for precise selection.

#### List the tracking information

Print out the all tracking information, the simple version:

```bash
paper_manager --list
```

or can use the single `--select` argument, such following command is equivalent to above command

```bash
paper_manager --select all
```

Search and print by keyword, author name, set title, tag, or file path and md5.

```bash
paper_manager --select [var, ...]
```

Using file path of md5 will obtain the *precise result*, which can use for modify file description.

#### Set Title and Keyword

In adding phase, the tracking item will be named as file name.

We can select the single *designated* item by precise argument (md5/path) to set name (title), such that

```bash
paper_manager --select [ md5 | <file name> ] --name The title want to name
```
Using `--keyword` can append the keyword into tracking record to all selected target.

```bash
paper_manager --select [var, ...] --keyword [keyword1 keyword2 ...]
```

Using `--author` can append the authors, and use `,` to distinguish multiple authors. 

```bash
paper_manager --select [var, ...] --author [author1, author2_first_name author2_last_name, author3, ...] 
```

To set the read status can use following command

```bash
paper_manager --select [var, ...] --read <read_status>
```

#### Get specific file tracked status

To check specific file tracked status can use the method same as searh and print information.

```bash
paper_manager --select <file name>
```

or we can use `--check` command such like

```bash
paper_manager --check <file name>
```

The difference between these method is that `--check` command will print extend tracking message, and `--select` can get multiple file status.

Finally, we also can use command `--open` to open pdf file in precise mode.

```bash
paper_manager --select [ md5 | <file name> ] --open 
```

and we also can use `--opendir` to open the directory of file at the same time.

```bash
paper_manager --select [ md5 | <file name> ] --open --opendir
```

> Currently, the `--open` feature only support `open` in mac and `explorer.exe` in windows or WSL.
> In the future, it can set the default `--open` command by other command using config file.

However, current method should set the opening command in the source code, in the future it will can be set by command and config file.

**Note**: Above commands which depend on `--select` can not use at the same time.

### Advance Feature

This program also support bibliography management by `BibTeX` format, and manage your review article in `append` mode or `overwrite` mode.

Beside the bibliography management, some of abovementioned command can also operate in different mode.

On the other hands, the tag feature can improve selecting enfficency and package the work.

#### Write information by default editor

Some information has long text that can not be key-in with CLI arguments.

Here provide a command `--write` can import the contents from the text file.

```bash
paper_manager --select [md5 | <file name>] --write <type>
```

There are 3 type can be support to use `--write` to modify the contents:  
- `bib` : The BibTeX format information, which will use to export the `.bib` file.
- `abs`/`abstract` : The paper abstract content, text format.
- `review` : The paper review write by youself, which can write by markdown format.

#### Import information from file

If user used to write the information in the other way, or need the explicit file for reading.

Here is providing a command `--get_in` can import the contents from the text file.

```bash
paper_manager --select [md5 | <file name>] --get_in <type> <file name>
```

There are 3 type can be support to use `--get_in` to import the contents:  
- `bib` : The BibTeX format information, which will use to export the `.bib` file.
- `abs`/`abstract` : The paper abstract content, text format.
- `review` : The paper review write by youself, which can write by markdown format.

#### Export information by designated format

The most recorded contents can use `--export` command to fetch.

This command also depends the selected targets, and implements designated opreation.

```bash
paper_manager --select [var, ...] --export <type>
```

**Note**: The exported file will create under current directory.

Basically, `--export` supports following types:  
- `pdf`: The files of selected items record, each item only one file will be exported.
- `bib`: A `.bib` file will be exported, it is collecting the bibliography witch import into selected items.
- `review`: A markdown format file includes review information will be exported.
- `abs`/`abstract`: A markdown format file includes abstract information will be exported.
- `md`/`markdown`: A markdown file consists of review and abstract will be exported.
- `blank`: Create blank markdown files which has md5 in file name for **every** selected result.

> The `--export` command only export a single file for designated type.   
> If the selected files more than one, it will create a compression `.zip` file. 

#### Action mode

Using `--mode` command can explicitly decide the action mode in `add`, `set` or `rm`.

In default situation, every operation can change mode is operating in `add` mode, i.e, append the content into record.

The usage of mode changing is

```bash
paper_manager --select [var, ...] --<operation> [content, ...] --mode [add | set | rm]
```

In the `add` mode, the contents will append into record, `set` mode the contents will overwrite on origin contents, and `rm` mode will remove the designated contents.

In following, we will show the different operation is supporting different mode

|Command|add|set|rm|
|:-----:|:-:|:-:|:-:|
|--author|O|O|O|
|--keyword|O|O|O|
|--get_in abs|X|O|X|
|--get_in bib|X|O|X|
|--get_in review|O|O|X|
|--export bib|O|O|X|
|--export abs|O|O|X|
|--export review|O|O|X|
|--read|X|O|O|
|--name|X|O|O|

> The behavior of `abstract` argument is same as `abs`.

#### Tag

The Tag is the keyword with specific format.

It can conduce to sort out the tracking items in the record, or package the designated files for the work wich need to export together.

We can use `@` perfix to set the Tag, such like

```bash
paper_manager --select [var, ...] --keyword @tag1
```

The tag will be not exported into the file, even it is record at keywords information.

Another property of Tag, we can use `@` to be a condition to select every tagged item.

```bash
paper_manager --select @
```

Therefore, we can use the command similar to following process to package multiple selected items in different time and export together.

```bash
paper_manager --select <condition 1> --keyword @1
paper_manager --select <condition 2> --keyword @1
paper_manager --select <file name> --keyword @1
paper_manager --select @1 --export <type>
```

Then finish the work, and need to remove the Tag, that can use following command. 

```bash
paper_manager --select @ --keyword @1 --mode rm
```

> In Future: We will update the `--tag` command to simplify process.

#### Selection of Inner-Join

In the above `--select` operation, it will select the union results for all arguments, i.e., when implements following command

```bash
paper_manager --select <condition 1> >> a.txt
paper_manager --select <condition 2> >> b.txt
paper_manager --select <condition 3> >> c.txt
```

then **union contents** of `a.txt`, `b.txt` and `c.txt`, will equivalent to
```bash
paper_manager --select <condition 1> <condition 2> <condition 3> 
```

After version v1.5, we provide the option `--inner` for selecting intersection of keyword which like inner join command of SQL.

Using command
```bash
paper_manager --select <condition 1> <condition 2> <condition 3> --inner
```
Then we can select the results that \<condition 1\>$\cap$\<condition 2\>$\cap$\<condition 3\>.

#### Filter

The selection filter provides a function to filter the selected results with some conditions.

In currently, we provide three common filter.

- `--is_read`: Filter the selected results is set `--read`.
- `--not_read`: Filter the selected results is not set or remove the `--read`.
- `--fixing`: Filter the selected results which is not have vaild file link.

> **Note**: Detail of `--fixing` will introduce in next section.

We can filter the selected results from `--select` by above arguments
```bash
paper_manager --select [var,...] [<--is_read | --not_read>, --fixing]
```

Besides above pre-defined filters, now, we can also use `--filters` command for customized filter at the same time.
```bash
paper_manager --select [var,...] [<pre-defined filters>] --filters [conditions,...]
```
The usable condictions is same as `--select`.


### Storing Architecture

In the beginning, we mentioned this program will manage the distributed file in centralized way.

When use `--add` command, it will record the `file name`, `absolute path`, `file hash code`(md5) in a JSON file in `~/.paper_manager`, and use md5 to be index.

At the same time, it will create the `file description XML file` under `~/.paper_manager/xml_repository/` directory.

The JSON file only records the information which can benefit for selecting process or relating file itself, such that
- Author name
- title
- keyword and tag
- is or not read
- path
- md5

The information for paper contents relating will be recorded into `file description XML file`, which make it conduces to write by human.
- title
- author name
- keyword
- abstract
- review

Due to the `file hash code` is exists in `file`, `JSON record` and `file description XML file`, these file can be decoupling.

Meanwhile, if we change the file name or change the path to the way is not recorded, the part of information will be lost.

The item lost some file information, we call that the item need to fix.

Here we provide some feature to conduce the fixing procedure.

#### Update and restore

**Q**: How to check the path is lost?

**A**: 

We provide the `--update` command to check all record path in each tracking item. 

```bash
paper_manager --update
```

Then, if the `file` path is lost, it will remove the path in the record; if the `file description XML file` is lost, it will search in `~/.paper_manager/xml_repository` directory to find whether the XML file record the same file hash code. Whereas the XML file is not exists, it will create a new XML file.

Subsequently, if the path record of tracking item are all removed, it will print out the message of file need to fix.

After above operating, we can use `--fixing` filter to find which record items need to fix.
```bash
paper_manager --select all --fixing
```

**Q**: How to fix the lost path?

**A**: 

Change the directory or rename the file, commonly it will impact few files. 

Using `--fixlink` command can can fix the single file link with designated directory or file.

```bash
paper_manager --fixlink <md5> [<file name> | <dir>]
```

**Q**: How to fix the multiple file?

**A**: 

In the situation of change the computer, change entire directory path or recover the backup file, that will impact path record of multiple files.

Then, it could implement the `--restore` command to fix tracking item by designated dirertory.

```bash
paper_manager --restore <directory>
```

In the restore procedure, it will implement the `--update` to remove invaild link, and fix link by `--fixlink <each md5> <dir>` sequentially.

#### Backup and git

The integral record consists of `file`, `JSON record` and `file description XML file`.

Using `--export` command can export all files of these three type by following command, respectively:

```bash
paper_manager --select all --export pdf #checkout all tracking pdf file
paper_manager --select all --export xml #checkout all tracking xml file
paper_manager --export stash            #checkout JSON record
```

Above commands will create two zip file and a JSON file.

Then, here we provide two commands to conduce the backup procedure.

```bash
paper_manager --select all --export backup     #JSON file and selected xml file
paper_manager --select all --export backup-all #JSON file and selected xml, pdf file
```

Consequently, we can use `--restore` command to recover tracking on the new environment.

After Version v1.8, the `--merge` command is support, which can use to merge XML file and JSON record.
```bash
paper_manager --merge [<backup json file | xml file> | <dir name>]
```

However, current program does not support a intelligently version management for the JSON and xml files.

The xml file merging just write the diff information into xml record, and mark up the tag `@+-`.

That do not support external protect safeguard, it may cause the undefined results.

Thus, we only suggest to merge JSON file, or single/few xml file.

For recover multiple backup, we can use `--restore` and `--merge` together.

```bash
paper_manager --merge <backup dir> #but we still do not suggest to do that when the status of xml file is uncertain
paper_manager --restore <backup dir> #recover file link for new merged record 
```

Futhermore, we still suggest to use `Git` or other powerful distributed version management software to implement this work.

### Other Command Support

#### Tracked the unnecessary file

Using `--add` on directory may track the unnecessary files, even the junk files.

After v1.8.1 we add the `--remove` features, which will only remove the tracking in JSON file by file names.

```bash
paper_manager --remove [<file name> , ...]
```

Then, because this command do not remove the xml files, at the same time we provide `--clear` to **show** the untracking XML files.

```bash
paper_manager --clear
```

