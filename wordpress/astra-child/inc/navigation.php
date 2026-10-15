<?php
/** Listener-first primary navigation, applied to existing Astra menus. */
if (!defined('ABSPATH')) { exit; }

function mirrortalk_navigation_key($item) {
    $title = strtolower(trim(wp_strip_all_tags((string) $item->title)));
    $path = strtolower((string) wp_parse_url((string) $item->url, PHP_URL_PATH));
    if ($path === '/' || $title === 'home') return 'home';
    if (strpos($path, '/listen') !== false || in_array($title, array('listen', 'podcast'), true)) return 'listen';
    if (strpos($path, 'podcast-episodes') !== false || in_array($title, array('episodes', 'explore'), true)) return 'explore';
    if (strpos($path, 'ask-mirror-talk') !== false || strpos($title, 'ask mirror talk') !== false) return 'ask';
    if (strpos($path, 'insights') !== false || $title === 'insights') return 'insights';
    if (strpos($path, 'contact') !== false || in_array($title, array('contact', 'connect'), true)) return 'connect';
    if (strpos($path, 'join') !== false || strpos($title, 'join us') !== false) return 'join';
    if (strpos($path, 'blog') !== false || strpos($path, 'explore') !== false || in_array($title, array('blog', 'explore'), true)) return 'explore';
    return 'other';
}

function mirrortalk_virtual_menu_item($id, $title, $path, $parent_id = 0) {
    return (object) array(
        'ID' => $id, 'db_id' => 0, 'menu_item_parent' => (string) $parent_id, 'object_id' => $id,
        'object' => 'custom', 'type' => 'custom', 'type_label' => __('Custom Link', 'astra-child'),
        'title' => $title, 'url' => home_url($path), 'target' => '', 'attr_title' => '',
        'description' => '', 'classes' => array('menu-item', 'menu-item-type-custom', 'mt-menu-' . sanitize_title($title)),
        'xfn' => '', 'status' => 'publish',
    );
}

function mirrortalk_listener_first_menu($items, $args) {
    $location = isset($args->theme_location) ? (string) $args->theme_location : '';
    if (!in_array($location, array('primary', 'primary-menu', 'menu-1'), true)) return $items;

    $present = array();
    $ask_parent_id = 0;
    foreach ($items as $item) {
        $key = mirrortalk_navigation_key($item);
        $present[$key] = true;
        if ((string) $item->menu_item_parent === '0') {
            if ($key === 'ask') $ask_parent_id = (int) $item->ID;
            if ($key === 'listen') { $item->title = __('Listen', 'astra-child'); $item->url = home_url('/listen/'); }
            if ($key === 'explore') $item->title = __('Explore', 'astra-child');
            if ($key === 'connect') $item->title = __('Connect', 'astra-child');
        }
    }
    if (empty($present['listen'])) $items[] = mirrortalk_virtual_menu_item(-9101, __('Listen', 'astra-child'), '/listen/');
    if (empty($present['insights'])) $items[] = mirrortalk_virtual_menu_item(-9102, __('Insights', 'astra-child'), '/insights/', $ask_parent_id);

    // Insights belongs to the Ask journey. If the editor has already nested it,
    // never manufacture a second top-level copy. If a top-level copy also
    // exists, keep only the nested one.
    $has_nested_insights = false;
    foreach ($items as $item) {
        if (mirrortalk_navigation_key($item) === 'insights' && (string) $item->menu_item_parent !== '0') {
            $has_nested_insights = true;
            break;
        }
    }
    if ($has_nested_insights) {
        $items = array_values(array_filter($items, function ($item) {
            return !(mirrortalk_navigation_key($item) === 'insights' && (string) $item->menu_item_parent === '0');
        }));
    }

    $priority = array('home' => 10, 'listen' => 20, 'explore' => 30, 'ask' => 40, 'insights' => 50, 'connect' => 60, 'other' => 70, 'join' => 80);
    $parents = array();
    foreach ($items as $item) {
        if ((string) $item->menu_item_parent === '0') $parents[(string) $item->ID] = mirrortalk_navigation_key($item);
    }
    $indexed = array_values($items);
    usort($indexed, function ($left, $right) use ($priority, $parents) {
        $left_key = (string) $left->menu_item_parent === '0' ? mirrortalk_navigation_key($left) : ($parents[(string) $left->menu_item_parent] ?? 'other');
        $right_key = (string) $right->menu_item_parent === '0' ? mirrortalk_navigation_key($right) : ($parents[(string) $right->menu_item_parent] ?? 'other');
        $group = ($priority[$left_key] ?? 70) <=> ($priority[$right_key] ?? 70);
        if ($group !== 0) return $group;
        $left_child = (string) $left->menu_item_parent !== '0';
        $right_child = (string) $right->menu_item_parent !== '0';
        if ($left_child !== $right_child) return $left_child ? 1 : -1;
        return ((int) ($left->menu_order ?? 0)) <=> ((int) ($right->menu_order ?? 0));
    });
    return $indexed;
}
add_filter('wp_nav_menu_objects', 'mirrortalk_listener_first_menu', 20, 2);
