import unittest
import photo_organizer

class TestPhotoOrganizer(unittest.TestCase):

  def test_object_creation(self):
      ph = photo_organizer.PhotoOrganizer(None)
      self.assertEqual(ph.paths, {})

  def test_simple_filenames(self):
      ph = photo_organizer.PhotoOrganizer(None)
      nf = ph.get_next_filename(r'c:\foo\bar\abc.jpg', 1)
      self.assertEqual(nf, r'c:\foo\bar\abc_1.jpg')

      nf = ph.get_next_filename(nf, 2)
      self.assertEqual(nf, r'c:\foo\bar\abc_2.jpg')

      nf = ph.get_next_filename(nf, 3)
      self.assertEqual(nf, r'c:\foo\bar\abc_3.jpg')

  def test_hard_filenames(self):
      ph = photo_organizer.PhotoOrganizer(None)
      nf = ph.get_next_filename(r'c:\foo\b_ar\abc.jpg', 1)
      self.assertEqual(nf, r'c:\foo\b_ar\abc_1.jpg')

      nf = ph.get_next_filename(r'c:\foo\b_ar\abc_2.jpg', 1)
      self.assertEqual(nf, r'c:\foo\b_ar\abc_2_1.jpg')

      nf = ph.get_next_filename(nf, 2)
      self.assertEqual(nf, r'c:\foo\b_ar\abc_2_2.jpg')

  def test_datetime_simple(self):
      ph = photo_organizer.PhotoOrganizer(None)
      dt = ph.get_datetime(r'1971:02:03 04:05:06+00:00',)
      self.assertEqual(dt.year, 1971)
      self.assertEqual(dt.month, 2)
      self.assertEqual(dt.day, 3)
      self.assertEqual(dt.hour, 4)
      self.assertEqual(dt.minute, 5)
      self.assertEqual(dt.second, 6)


if __name__ == '__main__':
    unittest.main()