import datetime


class DateNamer:
    def __init__(self, group_by="day", lang="english"):
        if group_by == "day":
            self.gb = 3
        elif group_by == "week":
            self.gb = 2
        elif group_by == "month":
            self.gb = 1
        elif group_by == "year":
            self.gb = 0
        else:
            raise ValueError("Cannot group by " + grop_by)

        if lang == "english":
            self.monthes = [
                "*",
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec"]
        elif lang == "russian":
            self.monthes = [
                "*",
                "Янв",
                "Фев",
                "Март",
                "Апр",
                "Май",
                "Июнь",
                "Июль",
                "Авг",
                "Сен",
                "Окт",
                "Ноя",
                "Дек"]
        elif lang == "ukrainian":
            self.monthes = [
                "*",
                "Сiч",
                "Лют",
                "Бер",
                "Квi",
                "Тра",
                "Чер",
                "Лип",
                "Сер",
                "Вер",
                "Жов",
                "Лис",
                "Гру"]
        else:
            raise ValueError("Unknown language: " + lang)

    def date_hash(self, date):
        if self.gb == 0:
            return date.year
        elif self.gb == 1:
            return date.month + 100 * date.year
        elif self.gb == 2:
            return (date - datetime.datetime(1970, 1, 5, 0, 0, 0, 1)).days // 7
        elif self.gb == 3:
            return date.day + 100 * date.month + 10000 * date.year

    def hash_date(self, date_hash):
        if self.gb == 0:
            return datetime.datetime(year=date_hash, month=1, day=1)
        elif self.gb == 1:
            return datetime.datetime(
                year=int(date_hash / 100),
                month=int(date_hash % 100),
                day=1)
        elif self.gb == 2:
            return datetime.datetime(1970, 1, 5, 0, 0, 0, 1) + \
                datetime.timedelta(days=7 * date_hash)
        elif self.gb == 3:
            return datetime.datetime(
                year=int(date_hash / 10000),
                month=(int(date_hash / 100) % 100),
                day=(date_hash % 100))

    def date_name(self, date_hash):
        if self.gb == 0:
            return str(date_hash)
        if self.gb == 1:
            return self.monthes[int(date_hash % 100)] + \
                " " + str(int(date_hash / 100))
        if self.gb == 2:
            monday = datetime.date(1970, 1, 5) + \
                datetime.timedelta(days=7 * date_hash)
            sunday = monday + datetime.timedelta(days=6)
            if monday.month == sunday.month:
                return "%s-%s %s %d" % (monday.day,
                                        sunday.day,
                                        self.monthes[monday.month],
                                        monday.year)
            elif monday.year == sunday.year:
                return "%s %s - %s %s %d" % (monday.day,
                                             self.monthes[monday.month],
                                             sunday.day,
                                             self.monthes[sunday.month],
                                             monday.year)
            else:
                return "%s %s %d - %s %s %d" % (monday.day,
                                                self.monthes[monday.month],
                                                monday.year,
                                                monday.day,
                                                self.monthes[sunday.month],
                                                sunday.year)
        elif self.gb == 3:
            return str(date_hash % 100) + " " + \
                self.monthes[int(date_hash / 100) % 100] + " " + \
                str(int(date_hash / 10000) % 100)
