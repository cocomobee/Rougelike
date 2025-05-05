import unittest
from unittest.mock import patch, Mock
from components.consumable import HealingConsumable
from exceptions import Impossible
from procgen import get_entities_at_random
from actions import ItemAction
import color


class TestGetEntitiesAtRandom(unittest.TestCase):
    @patch('procgen.random.choices')
    def test_includes_all_entities_up_to_floor_and_uses_correct_weights(self, mock_choices):
        weighted = {
            1: [('e1', 1), ('e2', 2)],
            2: [('e3', 3)]
        }
        # Force random.choices to return a known list
        mock_choices.return_value = ['e2', 'e3']

        result = get_entities_at_random(
            weighted_chances_by_floor=weighted,
            number_of_entities=2,
            floor=2)

        # Should return exactly what our mock gave
        self.assertEqual(result, ['e2', 'e3'])

        # And should have been called with entities ['e1','e2','e3'] and weights [1,2,3]
        mock_choices.assert_called_once_with(
            ['e1', 'e2', 'e3'],
            weights=[1, 2, 3],
            k=2
        )

    @patch('procgen.random.choices')
    def test_stops_at_floor_cutoff(self, mock_choices):
        weighted = {
            1: [('e1', 1), ('e2', 2)],
            3: [('e3', 3)]
        }
        mock_choices.return_value = ['e1']

        result = get_entities_at_random(weighted_chances_by_floor=weighted,
                                        number_of_entities=1,
                                        floor=1)

        self.assertEqual(result, ['e1'])
        mock_choices.assert_called_once_with(
            ['e1', 'e2'],
            weights=[1, 2],
            k=1
        )


class TestHealingConsumableActivate(unittest.TestCase):
    def setUp(self):
        # 1) Create the HealingConsumable component
        self.heal_comp = HealingConsumable(amount=5)

        # 2) Make a fake engine with a fake message_log
        fake_engine = Mock()
        fake_engine.message_log = Mock()

        # 3) Make a fake GameMap that holds our fake engine
        fake_map = Mock()
        fake_map.engine = fake_engine

        # 4) Make a fake Item (the component's parent) and wire up gamemap
        item = Mock()
        item.name = "TestPotion"
        item.gamemap = fake_map      # <— so BaseComponent.engine returns fake_engine
        self.heal_comp.parent = item

        # 5) Stub out consume() so it won't touch real inventory
        self.heal_comp.consume = Mock()

        # 6) Expose for assertions
        self.fake_engine = fake_engine

    def test_activate_successful_heal_logs_and_consumes(self):
        # Consumer only needs a fighter.heal() stub
        consumer = Mock()
        consumer.fighter = Mock()
        consumer.fighter.heal.return_value = 3

        action = ItemAction(consumer, self.heal_comp.parent)

        # Act
        self.heal_comp.activate(action)

        # Assert: message_log got called once with correct text & color
        expected = "You consume the TestPotion, and recover 3 HP!"
        self.fake_engine.message_log.add_message.assert_called_once_with(
            expected,
            color.health_recovered
        )

        # Assert: consume() was invoked once
        self.heal_comp.consume.assert_called_once()

    def test_activate_at_full_health_raises_impossible(self):
        consumer = Mock()
        consumer.fighter = Mock()
        consumer.fighter.heal.return_value = 0

        action = ItemAction(consumer, self.heal_comp.parent)

        with self.assertRaises(Impossible) as cm:
            self.heal_comp.activate(action)

        # No message, no consume
        self.fake_engine.message_log.add_message.assert_not_called()
        self.heal_comp.consume.assert_not_called()

        # Exception mentions “already full”
        self.assertIn("already full", str(cm.exception))


if __name__ == '__main__':
    unittest.main(verbosity=2)