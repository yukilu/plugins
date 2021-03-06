import wx
import json
import time
from threading import Thread
from wx.lib.pubsub import pub

import crawler
import myUtils
import pornDB

SETTING_FILENAME = 'setting.json'
DOWNLOADED_FILENAME = '91downloaded.txt'
SRC_FILENAME_TEMPLATE = '91pornSrc%d.txt'

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.InitUI()
    
    def InitUI(self):
        panel = wx.Panel(self)

        self.statusbar = self.CreateStatusBar()

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer()

        getBtn = wx.Button(panel, label='Get')
        self.getBtn = getBtn
        getBtn.Bind(wx.EVT_BUTTON, self.OnGetClick)
        copyBtn = wx.Button(panel, label='Copy')
        copyBtn.Bind(wx.EVT_BUTTON, self.OnCopy)
        self.copyBtn = copyBtn
        setBtn = wx.Button(panel, label='Setting')
        self.setBtn = setBtn
        setBtn.Bind(wx.EVT_BUTTON, self.OnSet)
        dbBtn = wx.Button(panel, label='Database')
        dbBtn.Bind(wx.EVT_BUTTON, self.OnDB)
        self.dbBtn = dbBtn
        bakBtn = wx.Button(panel, label='Backup')
        bakBtn.Bind(wx.EVT_BUTTON, self.OnBackup)
        self.bakBtn = bakBtn
        
        hbox.Add(getBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(copyBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(setBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(dbBtn, proportion=0, flag=wx.RIGHT, border=10)
        hbox.Add(bakBtn, proportion=0)

        tc = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tc = tc

        vbox.Add((0, 20))
        vbox.Add(hbox, proportion=0, flag=wx.ALIGN_CENTRE_HORIZONTAL, border=10)
        vbox.Add((0, 20))
        vbox.Add(tc, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(vbox)

        copyBtn.Disable()

        self.SetSize((900, 600))
        self.SetTitle('91porn Crawler')
        self.Center()
        self.Show(True)

        pub.subscribe(self.updateDisplay, 'update')

    def SendMsg(self, msg1, msg2=None):
        wx.CallAfter(pub.sendMessage, 'update', msg=(msg1, msg2))

    def OnGetClick(self, e):
        t = Thread(target=self.getClick)
        t.start()

    def getClick(self):
        self.getBtn.Disable()
        self.setBtn.Disable()
        self.bakBtn.Disable()

        setting = myUtils.read(SETTING_FILENAME)
        duration = setting['duration']
        item_amount = setting['itemAmount']
        domain = setting['domain']
        chosen = setting['chosen']

        serie = setting['series'][chosen]
        table = serie['title']
        initial_id = serie['itemId']
        page_index = serie['pageIndex']
        last_page = serie['lastPage']
        path = serie['path']

        self.SendMsg('script begins...', 'ready')
        self.SendMsg(f'Now time is {time.asctime()}\n')
        self.SendMsg(f'duration={duration}, item_amount={item_amount}, domain={domain}, chosen={chosen}')
        self.SendMsg(f'inital_id={initial_id}, page_index={page_index}, last_page={last_page}\n')

        if not initial_id:
            self.SendMsg(f'initializing table[{table}...]', f'table[{table}] initializing')
            pornDB.initialDB(table)
            initial_id += 1
            self.SendMsg(f'initialized table[{table}]', f'table[{table}] initialized')
            serie['itemId'] = initial_id
            myUtils.write(SETTING_FILENAME, setting, indent=2)
            self.SendMsg(f'{table}.itemId has been updated to 1\n')

        
        self.SendMsg(f'reading hrefs from table[{table}]...', 'hrefs reading...')
        hrefs = pornDB.readAllHrefs(table)
        hrefs_firstread_length = len(hrefs)
        self.SendMsg(f'read hrefs from table[{table} length={hrefs_firstread_length}\n', 'hrefs read')

        all_finished = page_index > last_page
        if hrefs_firstread_length == 0 and all_finished:
            self.SendMsg(f'table[{table}] all finished! You can reset it and get srcs a few days later')
            wx.MessageBox(f'table[{table}] all finished! You can reset it and get srcs a few days later',
                'Info', wx.OK | wx.ICON_INFORMATION)
            
            self.getBtn.Enable()
            self.setBtn.Enable()
            self.bakBtn.Enable()
            return

        if hrefs_firstread_length < item_amount and not all_finished:
            total = hrefs_firstread_length
            self.SendMsg(f'hrefs is not enough, get hrefs from {domain}...\n', 'hrefs getting...')
            crawler_hrefs = []
            
            while total < item_amount and page_index <= last_page:
                self.SendMsg(f'get {domain}{path} [page={page_index}] begins...')
                c_hrefs = crawler.getHref(path, domain, page_index , initial_id)
                self.SendMsg(f'got {domain}{path} [page={page_index}]\n')
                c_hrefs_length = len(c_hrefs)
                total += c_hrefs_length
                initial_id += c_hrefs_length
                page_index += 1
                crawler_hrefs += c_hrefs

                if duration:
                    time.sleep(duration)
            
            self.SendMsg(f'got hrefs from {domain}\n', 'hrefs got')
            self.SendMsg(f'adding hrefs to table[{table}]', 'hrefs adding...')
            pornDB.addHrefs(crawler_hrefs, table)
            self.SendMsg(f'added hrefs to table[{table}] successfully\n', 'hrefs added')

            serie['itemId'] = initial_id
            serie['pageIndex'] = page_index
            setting['lastModified'] = time.asctime()
            myUtils.write(SETTING_FILENAME, setting, indent=2)
            self.SendMsg(f'in table[{table}], itemId updated to {initial_id}, pageIndex updated to {page_index}\n')

            self.SendMsg(f'read hrefs from table[{table}] again...', 'hrefs reading again...')
            hrefs = pornDB.readAllHrefs(table)
            hrefs_length = len(hrefs)
            self.SendMsg(f'read hrefs from table[{table}], length is {hrefs_length}\n', 'hrefs read again')

        hrefs = hrefs[:item_amount]
        hrefs_length = len(hrefs)
        self.SendMsg(f'handle hrefs in table[{table}] done, length={hrefs_length}\n')

        self.SendMsg(f'get src in table[{table}] begins...\n', 'src getting...')
        counter = 0
        counter_get = 0
        srcs = []
        for href in hrefs:
            counter += 1
            url = domain + href['href']
            self.SendMsg(f'id={href["id"]}, itemIndex={href["itemIndex"]}, pageIndex={href["pageIndex"]}, counter={counter}')
            self.SendMsg(f'get {url} begins...')
            src = crawler.getSrc(url, self.error_callback)

            if src:
                counter_get += 1
                href['done'] = True
                srcs.append(src)
            self.SendMsg(f'got {url}')
            self.SendMsg(f'{src}\n')

            if duration:
                time.sleep(duration)
        
        box_msg = 'Sorry! Got nothing!'
        if counter_get:
            self.SendMsg(f'filter srcs from table[{table}] begins...', 'srcs filtering...')
            mp4s = myUtils.read(DOWNLOADED_FILENAME)
            self.SendMsg(f'mp4s has been loaded from {DOWNLOADED_FILENAME}, mp4s.length={len(mp4s)}')
            srcs_filtered = []
            mp4s_repeat = []
            mp4s_new = []
            for src in srcs:
                mp4 = myUtils.matchMp4(src)
                is_inserted = myUtils.insertIntoOrdered(mp4, mp4s)
                if is_inserted:
                    mp4s_new.append(mp4)
                    srcs_filtered.append(src)
                else:
                    mp4s_repeat.append(mp4)
                    self.SendMsg(f'{mp4}.mp4 has been downloaded before!')
                    self.SendMsg(f'(src = {src})')
            self.SendMsg(f'filtered srcs from table[{table}]\n', 'srcs filtered')

            counter_new = len(mp4s_new)
            counter_repeat = len(mp4s_repeat)

            if counter_repeat:
                self.SendMsg(f'{mp4s_repeat} repeated\n')
            else:
                self.SendMsg('none mp4 repeated\n')

            if counter_new:
                self.SendMsg(f'{mp4s_new} to be wrote into {DOWNLOADED_FILENAME}')
                self.SendMsg(f'write new mp4s into {DOWNLOADED_FILENAME}...', 'mp4s writing...')
                myUtils.write(DOWNLOADED_FILENAME, mp4s)
                self.SendMsg(f'write new mp4s into {DOWNLOADED_FILENAME} successfully!', 'mp4s wrote')
                self.SendMsg(f'now mp4s.length={len(mp4s)}\n')

                self.SendMsg(f'{mp4s_new} to be downloaded')
                self.SendMsg(f'got {counter_new} srcs(total {counter_get}, repeated {counter_repeat}) from table[{table}]',
                    'src got')
                box_msg = f'Enjoy! Got {counter_new} srcs(total {counter_get}, repeated {counter_repeat}) from table[{table}]'

                srcTxt = '\n'.join(srcs_filtered)
                myUtils.write(SRC_FILENAME_TEMPLATE % myUtils.getTimeStamp(), srcTxt, file_type='string')
                self.srcTxt = srcTxt
                self.SendMsg(f'{srcTxt}\n')

                self.copyBtn.Enable()
            else:
                self.SendMsg('got no new mp4s\n')
                self.SendMsg('nothing to be downloaded')

            ids = myUtils.filterIds(hrefs)
            self.SendMsg(f'{ids} prepared to delete in table[{table}]')
            self.SendMsg(f'delete hrefs from table[{table}] begins...', 'hrefs deleting...')
            pornDB.deleteHrefs(ids, table)
            self.SendMsg(f'deleted hrefs from table[{table}]\n', 'hrefs deleted')

            self.SendMsg('All done! Enjoy!', 'done')
        else:
            self.SendMsg('So sad! None src got!\n', 'done')
        
        self.SendMsg(f'Now time is {time.asctime()}\n')
        wx.MessageBox(box_msg, 'Info', wx.OK | wx.ICON_INFORMATION)

        self.getBtn.Enable()
        self.setBtn.Enable()
        self.bakBtn.Enable()
    
    def error_callback(self, error):
        self.StatusDisplay(f'{error}')
    
    def OnCopy(self, e):
        data = wx.TextDataObject()
        data.SetText(self.srcTxt)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
            self.statusbar.SetStatusText('src text copied to clipboard')
        else:
            wx.MessageBox('Unable to open the clipboard', 'Error', wx.OK | wx.ICON_ERROR)
    
    def OnSet(self, e):
        dial = MyDialog(None, title='Setting')
        dial.ShowModal()
        dial.Destroy()
    
    def OnDB(self, e):
        dial = DatabaseDialog(None, title='Database')
        dial.ShowModal()
        dial.Destroy()
    
    def OnBackup(self, e):
        dial = wx.MessageDialog(None,
            f'Are you sure to backup {SETTING_FILENAME} and {DOWNLOADED_FILENAME}, this will cover old backup files',
            'Warning', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return
        
        self.StatusDisplay(f'back up {SETTING_FILENAME} and {DOWNLOADED_FILENAME} begins...', 'backuping...')
        myUtils.backup(SETTING_FILENAME, indent=2)
        myUtils.backup(DOWNLOADED_FILENAME)
        self.StatusDisplay(f'back up {SETTING_FILENAME} and {DOWNLOADED_FILENAME} successfully!', 'backup successfully')
        wx.MessageBox(f'back up {SETTING_FILENAME} and {DOWNLOADED_FILENAME} successfully!', 'Info',
            wx.OK | wx.ICON_INFORMATION)
    
    def updateDisplay(self, msg):
        self.StatusDisplay(*msg)

    def StatusDisplay(self, txt, statusTxt=None):
        self.tc.AppendText(txt + '\n')
        if statusTxt:
            self.statusbar.SetStatusText(statusTxt)

class MyDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.setting = myUtils.read(SETTING_FILENAME)
        self.setting_widgets = {}
        self.serie_labels = [key for key in self.setting['series'][0]]
        self.set_labels = ['itemAmount', 'duration', 'domain', 'lastPage', 'path']
        self.InitUI()
    
    def InitUI(self):
        setting = self.setting
        CHOICES = [x['title'] for x in self.setting['series']]
        serie = setting['series'][setting['chosen']]
        self.selected_serie_index = serie['index']
        setting_widgets = self.setting_widgets

        panel = wx.Panel(self)
        grid = wx.GridBagSizer(10, 10)

        st1 = wx.StaticText(panel, label='ItemAmount')
        grid.Add(st1, pos=(1, 0), flag=wx.LEFT | wx.TOP, border=5)
        sc1 = wx.SpinCtrl(panel, value=str(setting['itemAmount']))
        setting_widgets['itemAmount'] = sc1
        grid.Add(sc1, pos=(1, 1))
        st2 = wx.StaticText(panel, label='Duration')
        grid.Add(st2, pos=(1, 2), flag=wx.LEFT | wx.TOP, border=5)
        sc2 = wx.SpinCtrl(panel, value=str(setting['duration']))
        setting_widgets['duration'] = sc2
        grid.Add(sc2, pos=(1, 3))

        st4 = wx.StaticText(panel, label='Domain')
        grid.Add(st4, pos=(2, 0), flag=wx.LEFT | wx.TOP, border=5)
        tc1 = wx.TextCtrl(panel, value=setting['domain'])
        setting_widgets['domain'] = tc1
        grid.Add(tc1, pos=(2, 1), span=(1, 3), flag=wx.EXPAND)

        st5 = wx.StaticText(panel, label='Chosen')
        grid.Add(st5, pos=(3, 0), flag=wx.LEFT | wx.TOP, border=5)
        cb = wx.ComboBox(panel, value=serie['title'], choices=CHOICES, style=wx.CB_READONLY)
        cb.Bind(wx.EVT_COMBOBOX, self.OnSelect)
        grid.Add(cb, pos=(3, 1))

        sbox = wx.StaticBox(panel, label='ChosenSeries')
        ssizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)

        serie_labels = self.serie_labels
        serie_labels_length = len(serie_labels)
        for serie_label in serie_labels:
            hbox = wx.BoxSizer()
            sst1 = wx.StaticText(panel, label=serie_label + ':')
            border = 3
            if serie_label == 'lastPage':
                sst2 = wx.TextCtrl(panel, value=str(serie[serie_label]))
            elif serie_label == 'path':
                sst_empty = wx.StaticText(panel, size=(-1, 5))
                ssizer.Add(sst_empty)

                sst2 = wx.TextCtrl(panel, value=serie[serie_label], size=(400, -1))
            else:
                border = 0
                sst2 = wx.StaticText(panel, label=str(serie[serie_label]))
                
            setting_widgets[serie_label] = sst2
            hbox.Add(sst1, flag=wx.TOP, border=border)
            hbox.Add(sst2, flag=wx.LEFT, border=10)
            ssizer.Add(hbox, flag=wx.LEFT, border=15)

        grid.Add(ssizer, pos=(5, 0), span=(serie_labels_length, 4), flag=wx.EXPAND | wx.LEFT, border=10)

        sBtn = wx.Button(panel, label='Save', id=wx.ID_SAVE)
        sBtn.Bind(wx.EVT_BUTTON, self.OnSave)
        cBtn = wx.Button(panel, label='Close', id=wx.ID_CLOSE)
        cBtn.Bind(wx.EVT_BUTTON, self.OnClose)
        btn_pos = serie_labels_length + 6
        grid.Add(sBtn, pos=(btn_pos, 1), flag=wx.ALIGN_CENTER)
        grid.Add(cBtn, pos=(btn_pos, 2), flag=wx.ALIGN_CENTER)

        panel.SetSizer(grid)

        self.SetSize(520, 480)
        self.Center()
        self.Show(True)
    
    def OnSelect(self, e):
        setting = self.setting
        setting_widgets = self.setting_widgets
        serie = myUtils.find(e.GetString(), setting['series'], 'title')
        self.selected_serie_index = serie['index']
        for p in self.serie_labels:
            setting_widgets[p].SetLabel(str(serie[p]))
    
    def OnSave(self, e):
        setting = self.setting
        setting_widgets = self.setting_widgets
        selected_serie_index = self.selected_serie_index
        setting['chosen'] = selected_serie_index
        serie = setting['series'][selected_serie_index]

        for w in self.set_labels:
            v = setting_widgets[w].GetValue()
            if w == 'domain':
                new_v = myUtils.handleDomain(v)
                setting_widgets[w].SetValue(new_v)
            elif w == 'path':
                new_v = myUtils.handleUrl(v)
                setting_widgets[w].SetValue(new_v)
            else:
                new_v = int(v)
            
            if new_v == None:
                wx.MessageBox(f'{w} is wrong, please write again', 'Error', style=wx.OK | wx.ICON_ERROR)
                return

            if w in self.serie_labels:
                serie[w] = new_v
            else:
                setting[w] = new_v
        
        setting['lastModified'] = time.asctime()
        myUtils.write(SETTING_FILENAME, setting, indent=2)
        wx.MessageBox('setting.json saved successfully', 'Info', wx.OK | wx.ICON_INFORMATION)

    def OnClose(self, e):
        self.Close()

class DatabaseDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.setting = myUtils.read(SETTING_FILENAME)
        self.series = self.setting['series']
        self.selected_serie = self.series[self.setting['chosen']]
        self.table = self.selected_serie['title']
        self.tables = list(map(lambda s: s['title'], self.series))
        self.InitUI()
    
    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer()
        st = wx.StaticText(panel, label='table:')
        cb = wx.ComboBox(panel, value=self.table, choices=self.tables, style=wx.CB_READONLY)
        cb.Bind(wx.EVT_COMBOBOX, self.OnSelect)

        removeBtn = wx.Button(panel, label='Remove')
        removeBtn.Bind(wx.EVT_BUTTON, self.OnRemove)
        resetBtn = wx.Button(panel, label='Reset')
        resetBtn.Bind(wx.EVT_BUTTON, self.OnReset)
        insertMp4Btn = wx.Button(panel, label='HanldeMp4')
        insertMp4Btn.Bind(wx.EVT_BUTTON, self.OnHandleMp4)
        hbox.Add(st, flag=wx.TOP | wx.RIGHT, border=5)
        hbox.Add(cb, flag=wx.TOP | wx.RIGHT, border=3)
        hbox.Add(removeBtn, flag=wx.LEFT, border=40)
        hbox.Add(resetBtn, flag=wx.LEFT, border=10)
        hbox.Add(insertMp4Btn, flag=wx.LEFT, border=10)
        vbox.Add(hbox, flag=wx.ALL, border=10)

        txt = self.GetTxt()
        tc = wx.TextCtrl(panel, value=txt, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tc = tc
        vbox.Add(tc, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        panel.SetSizer(vbox)

        self.SetSize(1000, 500)
        self.Center()
        self.Show(True)
    
    def OnSelect(self, e):
        self.table = e.GetString()
        self.selected_serie = myUtils.find(self.table, self.series, 'title')
        self.tc.SetValue(self.GetTxt())
    
    def OnReset(self, e):
        setting = self.setting
        table = self.table
        selected_serie = self.selected_serie

        dial = wx.MessageDialog(None, f'Are you sure to reset table[{table}]', 'Warning',
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return

        if not selected_serie['itemId']:
            wx.MessageBox(f'table[{table}] has not been initialized', 'Info', wx.OK | wx.ICON_INFORMATION)
            return
        
        self.tc.SetValue(f'table={table}, length=0\n')
        pornDB.clearHrefs(table)

        selected_serie['itemId'] = 1
        selected_serie['pageIndex'] = 1
        setting['lastModified'] = time.asctime()
        myUtils.write(SETTING_FILENAME, setting, indent=2)
        wx.MessageBox(f'table[{table}] has been reset!', 'Info', wx.OK | wx.ICON_INFORMATION)
    
    def OnRemove(self, e):
        dial = DatabaseRemoveDialog(self.table, None, title=f'Remove items in table[{self.table}]')
        dial.ShowModal()
        dial.Destroy()

        self.tc.SetValue(self.GetTxt())
    
    def OnHandleMp4(self, e):
        dial = HandleMp4Dialog(None)
        dial.ShowModal()
        dial.Destroy()

    def GetTxt(self):
        table = self.table
        
        if not self.selected_serie['itemId']:
            return f'table[{table}] has not initialized'

        hrefs = pornDB.readAllHrefs(table)
        hrefs_length = len(hrefs)
        for href in hrefs:
            del href['done']
        txt = myUtils.dictArray2str(hrefs)
        return f'table={table}, length={hrefs_length}\n\n{txt}\n'

class DatabaseRemoveDialog(wx.Dialog):
    def __init__(self, table, *args, **kw):
        super().__init__(*args, **kw)
        self.table = table
        self.InitUI()
    
    def InitUI(self):
        panel = wx.Panel(self)

        st1 = wx.StaticText(panel, label='ids:', pos=(50, 33))
        tc1 = wx.TextCtrl(panel, pos=(100, 30))
        self.startTc = tc1
        st2 = wx.StaticText(panel, label='~', pos=(230, 33))
        tc2 = wx.TextCtrl(panel, pos=(260, 30))
        self.endTc = tc2
        removeBtn = wx.Button(panel, label='Remove', pos=(110, 90))
        removeBtn.Bind(wx.EVT_BUTTON, self.OnRemove)
        closeBtn = wx.Button(panel, label='Close', pos=(230, 90))
        closeBtn.Bind(wx.EVT_BUTTON, self.OnClose)

        self.SetSize(450, 180)
        self.Center()
        self.Show(True)
    
    def OnRemove(self, e):
        try:
            start = int(self.startTc.GetValue())
            end = int(self.endTc.GetValue())
        except:
            wx.MessageBox('Please enter number!', 'Error', wx.OK | wx.ICON_ERROR)
            return
        
        if start > end:
            wx.MessageBox('Please ensure start is less than end', 'Error', wx.OK | wx.ICON_ERROR)
            return

        table = self.table
        dial = wx.MessageDialog(None, f'Are you sure to delete hrefs[ids={start}->{end}] in table[{table}]', 'Warning',
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return
        
        ids = range(start, end + 1)
        pornDB.deleteHrefs(ids, table)
        wx.MessageBox(f'hrefs[id={start}->{end}] in table[{table}] have been deleted successfully!', 'Info',
            wx.OK | wx.ICON_INFORMATION)
    
    def OnClose(self, e):
        self.Close()

class HandleMp4Dialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.InitUI()
    
    def InitUI(self):
        panel = wx.Panel(self)

        st1 = wx.StaticText(panel,
            label='Please type mp4 names(seperate by ",", eg: 3575, 5698, 93456) or txt file name(eg: d.txt)',
            pos=(10, 20))
        tc1 = wx.TextCtrl(panel, pos=(10, 45), size=(560, -1))
        self.inputTc = tc1
        st2 = wx.StaticText(panel, pos=(10, 90))
        self.st = st2
        tc2 = wx.TextCtrl(panel, pos=(10, 115), size=(560, 270), style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.showTc = tc2
        insertBtn = wx.Button(panel, label='Insert', pos=(140, 410))
        insertBtn.Bind(wx.EVT_BUTTON, self.OnInsert)
        removeBtn = wx.Button(panel, label='Remove', pos=(250, 410))
        removeBtn.Bind(wx.EVT_BUTTON, self.OnRemove)
        findBtn = wx.Button(panel, label='find', pos=(360, 410))
        findBtn.Bind(wx.EVT_BUTTON, self.OnFind)

        self.ShowMp4()

        self.SetTitle(f'Handle mp4s in {DOWNLOADED_FILENAME}')
        self.SetSize(600, 500)
        self.Center()
        self.Show(True)
    
    def OnInsert(self, e):
        targets = self.handleMp4str()
        if not targets:
            return
        
        dial = wx.MessageDialog(None, f'Are you sure to insert mp4s{targets} into {DOWNLOADED_FILENAME}', 'Warning',
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return
        
        insert_success, insert_fail = myUtils.insertIntoOrderedFile(targets, DOWNLOADED_FILENAME)

        if insert_success and insert_fail:
            msg1 = f'{insert_success} inserted successfully, '
            msg2 = f'{insert_fail} alreday exist'
        elif insert_fail:  # insert_success is empty
            msg1 = 'nothing inserted, '
            msg2 = f'{insert_fail} all already exist'
        elif insert_success:  # insert_fail is empty
            msg1 = f'{insert_success} all inserted successfully'
            msg2 = ''
        msg = f'In {DOWNLOADED_FILENAME} mp4s, {msg1}{msg2}!'
        self.inputTc.Clear()
        wx.MessageBox(msg, 'Info', wx.OK | wx.ICON_INFORMATION)
        self.ShowMp4(msg)

    def OnRemove(self, e):
        targets = self.handleMp4str()
        if not targets:
            return

        dial = wx.MessageDialog(None, f'Are you sure to remove mp4s{targets} in {DOWNLOADED_FILENAME}', 'Warning',
            wx.OK | wx.ICON_WARNING)
        ret = dial.ShowModal()
        if ret == wx.ID_NO:
            return
        
        r = myUtils.removeInFile(targets, DOWNLOADED_FILENAME)
        if not r:
            wx.MessageBox(f'mp4s read from {DOWNLOADED_FILENAME} is empty. So you can\'t remove anything in it!', 'Warning',
                wx.OK | wx.ICON_WARNING)
            return

        remove_success, remove_fail = r
        if remove_success and remove_fail:
            msg1 = f'{remove_success} removed successfully, '
            msg2 = f'{remove_fail} don\'t exist'
        elif remove_fail:  # remove_success is empty
            msg1 = f'nothing removed, '
            msg2 = f'{remove_fail} all don\'t exist'
        elif remove_success:
            msg1 = f'{remove_success} all removed successfully'
            msg2 = ''
        
        msg = f'In {DOWNLOADED_FILENAME} mp4s, {msg1}{msg2}!'
        self.inputTc.Clear()
        wx.MessageBox(msg, 'Info', wx.OK | wx.ICON_INFORMATION)
        self.ShowMp4(msg)

    def OnFind(self, e):
        targets = self.handleMp4str()
        if not targets:
            return

        r = myUtils.findInFile(targets, DOWNLOADED_FILENAME)
        if not r:
            wx.MessageBox(f'mp4s read from {DOWNLOADED_FILENAME} is empty. So you can\'t find anything in it!', 'Warning',
                wx.OK | wx.ICON_WARNING)
            return

        found, not_found = r
        msg = f'{found} in {DOWNLOADED_FILENAME}\n{not_found} not in {DOWNLOADED_FILENAME}'
        if not found:
            msg = f'{targets} are all not in {DOWNLOADED_FILENAME}'
        if not not_found:
            msg = f'{targets} all have been in {DOWNLOADED_FILENAME}'

        wx.MessageBox(msg, 'Info', wx.OK | wx.ICON_INFORMATION)

    def ShowMp4(self, msg=''):
        mp4s = myUtils.read(DOWNLOADED_FILENAME)
        length = len(mp4s)
        if msg:
            msg += '\n\n'
        txt = f'{msg}{mp4s}'
        self.showTc.SetValue(txt)
        self.st.SetLabel(f'mp4s[length={length}] in {DOWNLOADED_FILENAME}')

    def handleMp4str(self):
        mp4s_str = self.inputTc.GetValue()
        if '.txt' in mp4s_str:
            targets = myUtils.read(mp4s_str)
        else:
            targets = myUtils.str2ints(mp4s_str, ',')
        if not targets:
            wx.MessageBox('Wrong format, please type mp4s again!(eg: 123, 223, 305)', 'Error', wx.OK | wx.ICON_ERROR)
            return
        return targets

if __name__ == '__main__':
    app = wx.App()
    MyFrame(None)
    app.MainLoop()