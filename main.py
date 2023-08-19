import customtkinter as CTk
import threading
import os
import py7zr
import shutil
import time
import asyncio
from async7zip import async7zip, ReturnCodes7zip


class MyCheckboxFrame(CTk.CTkFrame):
    def __init__(self, master, title, values):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.title = title
        self.checkboxes = []

        self.title = CTk.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        for i, value in enumerate(self.values):
            checkbox = CTk.CTkCheckBox(self, text=value, state="normal", command=self.get)
            checkbox.grid(row=i+1, column=0, padx=10, pady=(10, 10), sticky="w")
            self.checkboxes.append(checkbox)


    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
            else:
                checkbox.configure(state="disabled")       
        if checked_checkboxes == []:
            for checkbox in self.checkboxes:
                checkbox.configure(state="normal")
        return checked_checkboxes

class StatisticFrame(CTk.CTkFrame):
    def __init__(self, master, title, values):
        super().__init__(master)
        self.grid_columnconfigure((0, 1), weight=1)
        self.title = title
        self.values = values

        for i, (text, volue) in enumerate(zip(self.title, self.values)):
                self.all_request_us = CTk.CTkLabel(self, text=text)
                self.all_request_us.grid(row=i+1, column=0,  padx=10, pady=10, sticky="w")
                self.all_request_us = CTk.CTkLabel(self, text=volue)
                self.all_request_us.grid(row=i+1, column=1,  padx=10, pady=10, sticky="w")                

class App(CTk.CTk):
    def __init__(self):
        super().__init__()
        
        self.geometry('600x600')
        self.title('Parser logs file')
        self.grid_columnconfigure((0, 1), weight=1) # for rows
        # self.grid_columnconfigure((0), weight=1) # for rows
        # self.rowconfigure((0,1), weight=1) 
        self.volue_checkbox = ["Парсінг US логу за IP", "Парсінг SE логу за 82opt"]  # "Повний аналіз логу US", "Повний аналіз логу SE"
        self.checkbox_frame = MyCheckboxFrame(self, title="Оберіть систему", values=self.volue_checkbox)
        self.checkbox_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.frame_file = CTk.CTkFrame(self)
        self.frame_file.grid(row=0, column=1, padx=(0, 10), pady=(10, 0), sticky="nsew")
        self.ip_address_entry = CTk.CTkEntry(self.frame_file, placeholder_text = "Введіть ІР адресу", state="normal")
        self.ip_address_entry.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        self.button_open_file = CTk.CTkButton(self.frame_file, text='Обрати файли', command=self.select_files)
        self.button_open_file.grid(row=2, column=0, padx=10, pady=10)
        self.count_files_label = CTk.CTkLabel(self.frame_file, text="Обрано файлів: 0")
        self.count_files_label.grid(row=3, column=0,  padx=10, pady=10)

        self.messege = CTk.CTkLabel(self, text="")
        self.messege.grid(row=2, column=0,  padx=10, pady=10, sticky="ew", columnspan=2)
        self.button_parser = CTk.CTkButton(self, text='Парсінг логів', state="disabled", command=self.parser)
        self.button_parser.grid(row=3, column=0, padx=10, pady=0, sticky="ew", columnspan=2)

        self.label_statistic = CTk.CTkLabel(self, text="Результат парсингу", fg_color="gray30", corner_radius=6)
        self.label_statistic.grid(row=4, column=0, padx=10, pady=(20, 0), sticky="ew", columnspan=2)

        
    def select_files(self):
        self.files = CTk.filedialog.askopenfilenames()
        self.button_parser.configure(state="normal")
        self.count_files_label.configure(text="Обрано файлів: " + str(len(self.files)))
        

    def thread(func):
        def wrapper(*args, **kwargs):
            current_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
            current_thread.daemon = True
            current_thread.start()

        return wrapper
    

    def messege_err(self):
        self.messege.configure(text="Трапилась помилка")
    
    def messege_err_ip(self):
        self.messege.configure(text="Введіть ІР адресу")

    def messege_err_type(self):
        self.messege.configure(text="Оберіть систему до якої відносяться логи")    
 
    
    @thread
    def parser(self):
        # Get the IP address from the input field
        self.ip_address = self.ip_address_entry.get()
        chosen_element = self.checkbox_frame.get()
        if chosen_element == []:
            self.messege_err_type()
            
        elif chosen_element == ["Парсінг US логу за IP"]:
            if self.ip_address == "":
                self.messege_err_ip()
            else:    
                self.run_parser(self.parser_us_file)  

        elif chosen_element == ["Парсінг SE логу за 82opt"]:
            if self.ip_address == "":
                self.messege_err_ip()
            else: 
                self.run_parser(self.parser_se_file)          


    def run_parser(self, type_log):
        self.button_parser.configure(state="disabled")            
        self.messege.configure(text="Зачекайте йде парсінг файлів")
        # start = time.perf_counter()
        self.create_file_list()
        type_log()
        # print(f"Запит зайняв: {time.perf_counter() - start}") 
        self.messege.configure(text="")
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        self.button_parser.configure(state="normal")                   
            

    def create_file_list(self):
        self.files_list = []
        self.tmp_dir = os.path.split(self.files[0])[0] + '/temp'
        try:
            for f in self.files:
                if os.path.splitext(f)[1] == '.7z':
                    with py7zr.SevenZipFile(f, "r") as myzip:
                        myzip.extractall(self.tmp_dir)   
                else:
                    self.files_list.append(f)

            try:
                if os.path.exists(self.tmp_dir):
                    list_tmp_dir = os.listdir(self.tmp_dir)
                    for tf in list_tmp_dir:
                        self.files_list.append(self.tmp_dir + '/' + tf)
            except:
                self.messege_err()         
            return self.files_list
        except Exception:
            self.messege_err()                                                  
                
    def parser_us_file(self):
        self.files_dir = os.path.split(self.files[0])[0] + '/'
        try:
            all_request = 0
            all_ok_request = 0
            for file in self.files_list:
                new_file_name = self.files_dir + self.ip_address + '_' + os.path.split(file)[1]
                with open(file, "r", encoding="UTF-8", errors='ignore') as f:
                    lines = []
                    should_write = False
                    for line in f:
                        match line:
                            case _ if self.ip_address in line and ": IN" in line and "ERR=0" in line and should_write == False:
                                should_write = True
                                lines.append(line)
                                all_ok_request += 1
                                all_request += 1
                            case _ if self.ip_address in line and ": IN" in line and should_write == False:
                                should_write = True
                                lines.append(line) 
                                all_request += 1
                            case _ if self.ip_address in line and ": IN" in line and should_write:
                                lines.append(line)
                                should_write = False
                            case _ if should_write:
                                lines.append(line)    

                if lines != []:
                    with open(new_file_name, "w", encoding="UTF-8") as f:
                        f.writelines(lines)

            if all_ok_request == all_request:
                err_count = 0
            elif all_ok_request == 0:
                err_count = all_request
            else:
                err_count = int((all_request - all_ok_request))    

            self.statistic_frame_us = StatisticFrame(self, title=['Всього запитів:', 'Кількість вдалих запитів:', 'Кількість помилок:'], values=[all_request, all_ok_request ,err_count])
            self.statistic_frame_us.grid(row=5, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)


        except Exception:
            self.messege_err()
    
    def parser_se_file(self):
        self.files_dir = os.path.split(self.files[0])[0] + '/'
        
        try:
            all_request = 0
            for file in self.files_list:
                new_file_name = self.files_dir + time.strftime("%Y%m%d-%H%M%S") + '_' + os.path.split(file)[1]
                with open(file, "r", encoding='UTF-8', errors='ignore') as f:
                    f_lines= []
                    s_line = False
                    lines = []
                    should_write = False
                    for line in f:
                        if "#1" in line:
                            should_write = True
                        elif "#7" in line and should_write:
                            lines.append(line)
                            should_write = False
                            if s_line:
                                for a in lines:
                                    f_lines.append(a)
                                s_line = False
                                lines.clear()
                            else:
                                lines.clear()
                        if should_write and self.ip_address in line :
                            lines.append(line)
                            s_line = True
                            all_request += 1
                        elif should_write:
                            lines.append(line)    
                if f_lines != []:
                    with open(new_file_name, "w", encoding="UTF-8") as f:
                        f.writelines(f_lines)
            self.statistic_frame_se = StatisticFrame(self, title=['Всього запитів:',], values=[all_request,])
            self.statistic_frame_se.grid(row=5, column=0, padx=10, pady=10, sticky="nsew", columnspan=2) 

        except Exception as ex:
            self.messege_err()
            
                            
if __name__ == '__main__':
    app = App()
    app.mainloop()

           