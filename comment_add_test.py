# -*- coding: utf-8 -*-
import unittest
import sys
import os, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from models import *

class CommentAddTest(unittest.TestCase):
    
    base_url = 'http://nsk.%s/' % os.getenv('SITE')
    ARTSOURCE = '%sartifact/' % os.getenv('BUILD_URL')
    driver = webdriver.Firefox()

    comment_values = {'comment': 'AutoTest User Comment',
                   'admin_answer': 'AutoTest ContentManager AnswerFromAdmin',
                   'public_answer': 'AutoTest ContentManager AnswerFromPublicSide'
                   }

    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    SCHEMA = os.getenv('SCHEMA')
    USER = os.getenv('USER')
    PSWD = os.getenv('PSWD')

    CONNECT_STRING = 'mysql://%s:%s@%s:%s/%s?charset=utf8' %(USER, PSWD, HOST, PORT, SCHEMA)
    engine = create_engine(CONNECT_STRING, echo=False) #Значение False параметра echo убирает отладочную информацию
    metadata = MetaData(engine)
    session = create_session(bind = engine)

    os.system('find -iname \*.png -delete')

    def tearDown(self):
        """Удаление переменных для всех тестов. Остановка приложения"""
        
        self.driver.close()
        if sys.exc_info()[0]:   
            print sys.exc_info()[0]

    def test_comment_add(self):
        driver = self.driver
        comment_values = self.comment_values
        cnt=0
        
        driver.get('%slogin' % self.base_url)
        time.sleep(5)
        driver.find_element_by_id('username').send_keys(os.getenv('AUTH'))
        driver.find_element_by_id('password').send_keys(os.getenv('AUTHPASS'))
        driver.find_element_by_class_name('btn-primary').click()
        time.sleep(5)

        #получения алиаса и id из БД
        good = self.session.query(Goods).\
               join(Goods_stat, Goods.id == Goods_stat.goods_id).\
               join(Region, Goods_stat.city_id == Region.id).\
               join(Goods_block, Goods.block_id == Goods_block.id).\
               join(Main_goods_prices, Goods.id == Main_goods_prices.goods_id ).\
               filter(Region.domain == 'nsk').\
               filter(Goods_stat.status == 1).\
               filter(Goods.overall_type == 0).\
               filter(Goods_block.delivery_type == 1).\
               filter(Main_goods_prices.price_type_guid == Region.price_type_guid).\
               filter(Main_goods_prices.price < 3000).\
               first()

        #переходим в публичную часть и оставляем отзыв
        driver.get('%sproduct/%s/' % (self.base_url, good.alias))

        #Установка рейтинга 5 и отправка запроса с отзывом
        driver.find_element_by_css_selector('#site_GoodsComment_form_rating_4 > a[title="5"]').click()
        driver.find_element_by_id('site_GoodsComment_form_comment').send_keys(comment_values['comment'])
        driver.find_element_by_css_selector('#writeComment > input.submitButton').click()

        #Переход в админку и отет на отзыв из админки
        driver.get('%sterminal/admin/site/terminal/tgoodscomment/list' % self.base_url)
        driver.find_element_by_link_text(comment_values['comment']).click()
        Select(driver.find_element_by_css_selector('select[id*="_status"]')).select_by_visible_text(u'Активен на сайте')#активируем отзыв
        driver.find_element_by_name('btn_update_and_edit').click()

        #отвечаем на отзыв
        driver.find_element_by_link_text(u'Новый ответ').click()
        driver.find_element_by_css_selector('textarea[id*="_comment"]').send_keys(comment_values['admin_answer'])
        driver.find_element_by_name('btn_create_and_edit').click()

        #driver.close()
        #driver = webdriver.Firefox()
        #driver.get('%slogin' % self.base_url)
        #time.sleep(5)
        #driver.find_element_by_id('username').send_keys(os.getenv('AUTH'))
        #driver.find_element_by_id('password').send_keys(os.getenv('AUTHPASS'))
        #driver.find_element_by_class_name('btn-primary').click()
        #time.sleep(5)



        #переходим в публичную часть и проверяем применился ли отзыв
        driver.get('%sproduct/%s/' % (self.base_url, good.alias))
        driver.refresh()
        comment = driver.find_element_by_css_selector('#tabTarget7 div:first-child')
        
        #проверяем комментарий пользователя
        if comment.find_element_by_class_name('user_comment').text.strip() != comment_values['comment']:
            cnt += 1
            print 'Некорректный отзыв'
            print 'На странице: ', comment.find_element_by_class_name('user_comment').text.strip()
            print 'Необходимо: ', comment_values['comment']
            print '*'*80

        #проверяем ответ на комментарий пользователя из админки
        if comment.find_elements_by_tag_name('div')[-1].find_elements_by_tag_name('p')[1].text.strip() != comment_values['admin_answer']:
            cnt += 1
            print 'Некорректный отзыв'
            print 'На странице: ', comment.find_elements_by_tag_name('div')[-1].find_elements_by_tag_name('p')[1].text.strip()
            print 'Необходимо: ', comment_values['admin_answer']
            print '*'*80

        #Отвечаем на отзыв от имени Терминал.ру из карточки товара
        comment.find_element_by_id('mother').click()
        comment_answer_dialog = driver.find_element_by_class_name('commentAnswerDialog')
        comment_answer_dialog.find_element_by_id('site_GoodsCommentAnswer_form_comment').send_keys(comment_values['public_answer'])
        comment_answer_dialog.find_element_by_class_name('submitButton').click()

        #ждем пока страница перезагрузится и появится ответ на отзыв из карточки товара
        time.sleep(10)
        comment = driver.find_element_by_css_selector('#tabTarget7 div:first-child')#обновляем данные, в кеше нет свежего отзыва

        #проверяем ответ на комментарий пользователя из карточки товара
        if comment.find_elements_by_tag_name('div')[-1].find_elements_by_tag_name('p')[1].text.strip() != comment_values['public_answer']:
            cnt += 1
            print 'Некорректный отзыв'
            print 'На странице: ', comment.find_elements_by_tag_name('div')[-1].find_elements_by_tag_name('p')[1].text.strip()
            print 'Необходимо: ', comment_values['public_answer']
            print '*'*80

            
        #удаляем 3 последних отзыва
        driver.get('%sterminal/admin/site/terminal/tgoodscomment/list' % self.base_url)
        driver.find_element_by_name('idx[]').click()
        driver.find_element_by_xpath('(//input[@name="idx[]"])[2]').click()
        driver.find_element_by_xpath('(//input[@name="idx[]"])[3]').click()
        time.sleep(5)
        Select(driver.find_element_by_name('action')).select_by_visible_text(u'Удалить')
        driver.find_element_by_css_selector('div.actions.sonata-ba-list-actions > input.btn.btn-primary').click()
        driver.find_element_by_css_selector('input.btn.btn-danger').click()

        for key in comment_values:
            try:
                driver.find_element_by_link_text(comment_values[key])
                cnt += 1
                print 'Отзыв не удалился'
                print 'Текст отзыва: ', comment_values[key]
                print '*'*80
            except:
                pass


        assert cnt==0, (u'Errors:%d')%(cnt)
        
        
        
       

