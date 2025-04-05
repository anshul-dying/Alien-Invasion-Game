import sys
import pygame
from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from time import sleep
from game_stats import GameStats
from button import Button

class AlienInvasion:
    """Constructor"""
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Alien Invasion")

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_width = self.screen.get_rect().width
        self.screen_height = self.screen.get_rect().height  
        self.settings = Settings()

        # Initialize sound mixer and load sound effects
        pygame.mixer.init()
        self.shoot_sound = pygame.mixer.Sound("sfx/shoot.wav")
        self.explosion_sound = pygame.mixer.Sound("sfx/explosion_min.wav")
        self.ship_explosion_sound = pygame.mixer.Sound("sfx/ship_explosion.mp3")

        self.stats = GameStats(self)
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        self.game_active = False
        self.font = pygame.font.SysFont(None, 36)
        self.play_button = Button(self, "Play")
        self.game_over_button = Button(self, "Game Over - Click to Restart")

    """Main Game Functions"""
    def run_game(self):
        while True:
            self._check_events()
            
            if self.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()
            self.clock.tick(60)

    def _check_events(self):
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    self._check_keydown_events(event)
                elif event.type == pygame.KEYUP:
                    self._check_keyup_events(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_play_button(mouse_pos)

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
            print(f"Moving Right {self.ship.rect.x}")
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
            print(f"Moving Left {self.ship.rect.x}")
    
    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
            print(f"Moving Stopped")
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
            print(f"Moving Stopped")
        elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullets()

    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)

        score_str = f"Score: {self.stats.score}"
        score_image = self.font.render(score_str, True, (0, 0, 0), self.settings.bg_color)
        self.screen.blit(score_image, (10, 10))

        lives_str = f"Lives: {self.stats.ships_left}"
        lives_image = self.font.render(lives_str, True, (0, 0, 0), self.settings.bg_color)
        self.screen.blit(lives_image, (10, 50))

        if not self.game_active:
            if self.stats.ships_left <= 0:
                self.game_over_button.draw_button()
            else:
                self.play_button.draw_button()
        pygame.display.flip()

    """Bullet functions"""
    def _fire_bullets(self):
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
            self.shoot_sound.play()

    def _update_bullets(self):
        self.bullets.update()

        """Get Rid of Bullets"""
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet  )
        self._check_bullet_alien_collisions( )

    def _check_bullet_alien_collisions(self):
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
        if collisions:
            self.stats.score += 10 * len(collisions)  # 10 points per alien hit
            self.explosion_sound.play()
        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
    
    """Alien and Ship Functions"""
    def _create_fleet(self):
        """Create a fleet of aliens in a staggered wave pattern."""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        # Define number of aliens per row and rows
        aliens_per_row = 8
        number_rows = 4

        # Calculate spacing
        x_spacing = alien_width * 2.5
        y_spacing = alien_height * 2

        # Starting positions
        current_x = alien_width
        current_y = alien_height

        for row_number in range(number_rows):
            if row_number % 2 == 0:
                offset = 1
            else:
                offset = alien_width * 1.25

            for alien_number in range(aliens_per_row):
                self._create_alien(current_x + offset + (alien_number * x_spacing), 
                                 current_y + (row_number * y_spacing))

    def _create_alien(self, x_position, y_position):
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)
    
    def _update_aliens(self):
        self._check_fleet_edges()
        self.aliens.update()

        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
            print("Ship Hit!!!!")
        self._check_aliens_bottom()
    
    def _check_fleet_edges(self):
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
    
    def _change_fleet_direction(self):
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
            self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                self._ship_hit()
                break

    def _ship_hit(self):
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1
            self.bullets.empty()
            self.aliens.empty()
            self._create_fleet()
            self.ship.center_ship()
            self.ship_explosion_sound.play()
            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)  # Changed from False to True
    
    """Button Functions"""
    def _check_play_button(self, mouse_pos):
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        game_over_clicked = self.game_over_button.rect.collidepoint(mouse_pos)
        if (button_clicked or game_over_clicked) and not self.game_active:
            self.stats.reset_stats()
            self.game_active = True
            self.bullets.empty()
            self.aliens.empty()
            self._create_fleet()
            self.ship.center_ship()
            pygame.mouse.set_visible(False)


if __name__ == "__main__":
    ai = AlienInvasion()
    ai.run_game()