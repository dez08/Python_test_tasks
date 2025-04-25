from django import template
from django.urls import resolve, Resolver404
from ..models import Menu, MenuItem

register = template.Library()


@register.inclusion_tag('tree_menu/menu.html', takes_context=True)
def draw_menu(context, menu_name):
    request = context['request']
    current_url = request.path_info

    try:
        menu = Menu.objects.prefetch_related('items').get(name=menu_name)
    except Menu.DoesNotExist:
        return {'menu': None}

    menu_items = menu.items.all()

    # Определяем активный пункт меню
    active_item = None
    try:
        resolved_url = resolve(current_url)
        for item in menu_items:
            if item.named_url and item.named_url == resolved_url.url_name:
                active_item = item
                break
            elif item.url and item.url == current_url:
                active_item = item
                break
    except Resolver404:
        pass

    # Строим дерево меню
    def build_menu_tree(items, parent=None):
        result = []
        for item in items:
            if item.parent == parent:
                children = build_menu_tree(items, item)
                is_active = (item == active_item) or any(child.get('is_active') for child in children)
                result.append({
                    'item': item,
                    'children': children,
                    'is_active': is_active,
                    'is_expanded': is_active,
                })
        return result

    menu_tree = build_menu_tree(menu_items)

    # Разворачиваем родителей активного пункта
    def expand_parents(tree):
        for node in tree:
            if node['is_active']:
                # Разворачиваем первый уровень вложенности под активным пунктом
                for child in node['children']:
                    child['is_expanded'] = True
                return True
            if expand_parents(node['children']):
                node['is_expanded'] = True
                return True
        return False

    expand_parents(menu_tree)

    return {
        'menu': menu,
        'menu_tree': menu_tree,
        'current_url': current_url,
    }