# alchPRO/services/calculator.py

class AlchCalculator:
    @staticmethod
    def process_items(mapping_data, prices_data, volume_data, nat_rune_cost):
        """Processes calculations for all valid game elements based on active formula rules."""
        calculated_items = []

        if not mapping_data or not prices_data:
            return calculated_items

        for item in mapping_data:
            alch_value = item.get("highalch", 0)
            if alch_value <= 0:
                continue

            item_id = str(item["id"])
            api_entry = prices_data.get(item_id)
            if not api_entry:
                continue

            raw_high = api_entry.get('high')
            raw_low = api_entry.get('low')

            if not raw_high and not raw_low:
                continue

            buy_price = int(raw_high) if raw_high else int(raw_low)
            sell_price = int(raw_low) if raw_low else buy_price

            # SMART OPTIMAL COST SELECTOR RULE
            if buy_price > 0 and sell_price > 0:
                best_cost = min(buy_price, sell_price)
            else:
                best_cost = buy_price if buy_price > 0 else sell_price

            if best_cost <= 0:
                continue

            # PROFIT FORMULA EQUATION MATRIX
            net_profit = alch_value - (best_cost + nat_rune_cost)

            vol_entry = volume_data.get(item_id)
            volume_1h = 0
            if vol_entry:
                volume_1h = vol_entry.get('highPriceVolume', 0) + vol_entry.get('lowPriceVolume', 0)

            calculated_items.append({
                'id': item_id,
                'name': item.get("name", "Unknown"),
                'high_price': buy_price,
                'low_price': sell_price,
                'best_cost': best_cost,
                'alch_value': alch_value,
                'nat_cost': nat_rune_cost,
                'net_profit': net_profit,
                'volume': volume_1h,
                'limit': item.get("limit", 0),
                'members': bool(item.get("members", False))
            })

        # DEFAULT SORTING: Highest net profit descending
        calculated_items.sort(key=lambda x: x['net_profit'], reverse=True)
        return calculated_items

    @staticmethod
    def fix_historical_profits(history_logs, calculated_items_cache):
        """Retroactively scrubs and fixes the batch profit for all historical logs."""
        alch_lookup = {item['name']: item['alch_value'] for item in calculated_items_cache}
        fixed_count = 0
        
        for log in history_logs:
            item_name = log['name']
            historical_nat_cost = log.get('nat_cost', 90)
           
            if item_name in alch_lookup:
                alch_val = alch_lookup[item_name]
                profit_per_cast = alch_val - (log['cost_paid'] + historical_nat_cost)
                correct_batch_profit = profit_per_cast * log['qty']
                
                if log['batch_profit'] != correct_batch_profit:
                    log['batch_profit'] = correct_batch_profit
                    fixed_count += 1
                    
        return fixed_count