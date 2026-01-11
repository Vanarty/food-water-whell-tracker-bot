"""
Модуль для создания графиков прогресса
"""
import io
from datetime import datetime, timedelta
from typing import List, Dict, Any
import matplotlib
matplotlib.use('Agg')  # Используем не-интерактивный бэкенд
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure


def create_water_progress_chart(history: List[Dict[str, Any]], 
                                  goal: int,
                                  today_consumed: int) -> io.BytesIO:
    """
    Создать график прогресса по воде за неделю
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Настройка стиля
    plt.style.use('seaborn-v0_8-whitegrid')
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    
    # Подготовка данных
    dates = []
    amounts = []
    
    # Создаём полный список дат за последние 7 дней
    today = datetime.now().date()
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        dates.append(date)
        
        # Ищем данные для этой даты
        amount = 0
        for h in history:
            if h['date'] == date.isoformat():
                amount = h['amount']
                break
        
        # Для сегодняшнего дня используем актуальные данные
        if date == today:
            amount = today_consumed
            
        amounts.append(amount)
    
    # Цвета для столбцов (зелёный если цель достигнута, синий если нет)
    colors = ['#4ecca3' if a >= goal else '#00d9ff' for a in amounts]
    
    # Построение столбчатой диаграммы
    bars = ax.bar(dates, amounts, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
    
    # Линия цели
    ax.axhline(y=goal, color='#ff6b6b', linestyle='--', linewidth=2, label=f'Цель: {goal} мл')
    
    # Добавляем значения над столбцами
    for bar, amount in zip(bars, amounts):
        height = bar.get_height()
        ax.annotate(f'{int(amount)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=10, fontweight='bold',
                    color='white')
    
    # Настройка осей
    ax.set_xlabel('Дата', fontsize=12, color='white', fontweight='bold')
    ax.set_ylabel('Вода (мл)', fontsize=12, color='white', fontweight='bold')
    ax.set_title('💧 Потребление воды за неделю', fontsize=16, color='white', fontweight='bold', pad=20)
    
    # Форматирование дат
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.tick_params(colors='white')
    
    # Легенда
    ax.legend(loc='upper right', facecolor='#16213e', edgecolor='white', labelcolor='white')
    
    # Установка лимитов
    ax.set_ylim(0, max(max(amounts) * 1.2, goal * 1.2))
    
    plt.tight_layout()
    
    # Сохранение в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    
    return buf


def create_calories_progress_chart(food_history: List[Dict[str, Any]],
                                    workout_history: List[Dict[str, Any]],
                                    goal: float,
                                    today_consumed: float,
                                    today_burned: float) -> io.BytesIO:
    """
    Создать график прогресса по калориям за неделю
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Настройка стиля
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    
    # Подготовка данных
    today = datetime.now().date()
    dates = []
    consumed = []
    burned = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        dates.append(date)
        
        # Потреблённые калории
        cons = 0
        for h in food_history:
            if h['date'] == date.isoformat():
                cons = h['calories']
                break
        
        # Сожжённые калории
        burn = 0
        for h in workout_history:
            if h['date'] == date.isoformat():
                burn = h['calories']
                break
        
        # Для сегодняшнего дня используем актуальные данные
        if date == today:
            cons = today_consumed
            burn = today_burned
            
        consumed.append(cons)
        burned.append(burn)
    
    # Позиции столбцов
    x = range(len(dates))
    width = 0.35
    
    # Построение столбцов
    bars1 = ax.bar([i - width/2 for i in x], consumed, width, 
                   label='Потреблено', color='#ff6b6b', alpha=0.8, edgecolor='white')
    bars2 = ax.bar([i + width/2 for i in x], burned, width, 
                   label='Сожжено', color='#4ecca3', alpha=0.8, edgecolor='white')
    
    # Линия цели
    ax.axhline(y=goal, color='#feca57', linestyle='--', linewidth=2, label=f'Цель: {int(goal)} ккал')
    
    # Добавляем значения над столбцами
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8, color='white')
    
    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8, color='white')
    
    # Настройка осей
    ax.set_xlabel('Дата', fontsize=12, color='white', fontweight='bold')
    ax.set_ylabel('Калории (ккал)', fontsize=12, color='white', fontweight='bold')
    ax.set_title('🔥 Калории за неделю', fontsize=16, color='white', fontweight='bold', pad=20)
    
    # Метки на оси X
    ax.set_xticks(x)
    ax.set_xticklabels([d.strftime('%d.%m') for d in dates])
    ax.tick_params(colors='white')
    
    # Легенда
    ax.legend(loc='upper right', facecolor='#16213e', edgecolor='white', labelcolor='white')
    
    # Установка лимитов
    max_val = max(max(consumed) if consumed else 0, max(burned) if burned else 0, goal)
    ax.set_ylim(0, max_val * 1.2)
    
    plt.tight_layout()
    
    # Сохранение в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    
    return buf


def create_combined_progress_chart(water_history: List[Dict[str, Any]],
                                    food_history: List[Dict[str, Any]],
                                    workout_history: List[Dict[str, Any]],
                                    water_goal: int,
                                    calorie_goal: float,
                                    today_water: int,
                                    today_consumed: float,
                                    today_burned: float) -> io.BytesIO:
    """
    Создать комбинированный график прогресса
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Настройка стиля
    fig.patch.set_facecolor('#1a1a2e')
    
    today = datetime.now().date()
    dates = []
    for i in range(6, -1, -1):
        dates.append(today - timedelta(days=i))
    
    # ===== ГРАФИК ВОДЫ =====
    ax1.set_facecolor('#16213e')
    
    water_amounts = []
    for date in dates:
        amount = 0
        for h in water_history:
            if h['date'] == date.isoformat():
                amount = h['amount']
                break
        if date == today:
            amount = today_water
        water_amounts.append(amount)
    
    colors = ['#4ecca3' if a >= water_goal else '#00d9ff' for a in water_amounts]
    bars = ax1.bar(dates, water_amounts, color=colors, alpha=0.8, edgecolor='white')
    ax1.axhline(y=water_goal, color='#ff6b6b', linestyle='--', linewidth=2)
    
    for bar, amount in zip(bars, water_amounts):
        height = bar.get_height()
        ax1.annotate(f'{int(amount)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, color='white')
    
    ax1.set_title('💧 Вода (мл)', fontsize=14, color='white', fontweight='bold')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax1.tick_params(colors='white')
    ax1.set_ylim(0, max(max(water_amounts) * 1.2, water_goal * 1.2))
    
    # ===== ГРАФИК КАЛОРИЙ =====
    ax2.set_facecolor('#16213e')
    
    consumed = []
    burned = []
    for date in dates:
        cons = 0
        burn = 0
        for h in food_history:
            if h['date'] == date.isoformat():
                cons = h['calories']
                break
        for h in workout_history:
            if h['date'] == date.isoformat():
                burn = h['calories']
                break
        if date == today:
            cons = today_consumed
            burn = today_burned
        consumed.append(cons)
        burned.append(burn)
    
    # Баланс калорий (потреблено - сожжено)
    balance = [c - b for c, b in zip(consumed, burned)]
    colors = ['#4ecca3' if bal <= calorie_goal else '#ff6b6b' for bal in balance]
    
    x = range(len(dates))
    width = 0.35
    
    ax2.bar([i - width/2 for i in x], consumed, width, label='Потреблено', color='#ff6b6b', alpha=0.8)
    ax2.bar([i + width/2 for i in x], burned, width, label='Сожжено', color='#4ecca3', alpha=0.8)
    ax2.axhline(y=calorie_goal, color='#feca57', linestyle='--', linewidth=2)
    
    ax2.set_title('🔥 Калории (ккал)', fontsize=14, color='white', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([d.strftime('%d.%m') for d in dates])
    ax2.tick_params(colors='white')
    ax2.legend(loc='upper right', facecolor='#16213e', edgecolor='white', labelcolor='white')
    
    max_val = max(max(consumed) if consumed else 0, calorie_goal)
    ax2.set_ylim(0, max_val * 1.2)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    
    return buf


