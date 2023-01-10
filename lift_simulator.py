import random
import time
import threading
import signal
import pygame


class Lift:
    def __init__(self):
        self.NUM_FLOORS = 11  # 0 - 10
        self.direction = 0  # 0 -> no direction, 1 -> up, 2 -> down
        self.current_pos = 0
        self.destination = 0
        self.buttons_pressed = [False] * self.NUM_FLOORS
        self.floor_requests = [0] * self.NUM_FLOORS
        self.up_timestamp = [None] * self.NUM_FLOORS
        self.down_timestamp = [None] * self.NUM_FLOORS
        self.exit = False
        self.WIDTH = 800
        self.HEIGHT = 600
        self.WHITE = (255, 255, 255)
        self.ORANGE = (255, 127, 80)
        self.BLACK = (0, 0, 0)
        self.GREY = (192,192,192)

        # 0 -> no request
        # 1 -> up
        # 2 -> down
        # 3 -> both

        pygame.init()

        self.open_img = pygame.image.load('intro_image.png')
        self.open_img = pygame.transform.scale(self.open_img, (self.WIDTH, self.HEIGHT))

        #self.bg = pygame.image.load('bg_image_2.png')
        #self.bg = pygame.transform.scale(self.bg, (800, 600))

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption('Lift Simulator')

    def scan_request(self, random_floor):
        # Produce a random floor request with random direction.
        # This is created by a sw thread representing each floor.
        random_button = random.choice([0, 1, 2, 3])

        if random_floor == 0:
            random_button = 1
        if random_floor == self.NUM_FLOORS - 1:
            random_button = 2
        if random_button != 0:
            # if there is already a request, ensure the new request doesn't nullify prev request
            if self.floor_requests[random_floor] == 0:
                self.floor_requests[random_floor] = random_button
            elif self.floor_requests[random_floor] == 1 and random_button >= 2:
                self.floor_requests[random_floor] = 3
            elif self.floor_requests[random_floor] == 2 and (random_button == 1 or random_button == 3):
                self.floor_requests[random_floor] = 3

        # print(f"Request at floor {random_floor} in dir {random_button}.")

    def lift_movement(self):
        # Main function that controls the life movement. It scans for a floor request from any floor.
        # self.reset_screen()
        self.screen.fill(self.BLACK)
        self.set_base_screen_right()
        pygame.display.update()

        while not self.exit:


            self.find_destination_on_floor_requests()
            if self.floor_requests.count(0) == self.NUM_FLOORS and self.buttons_pressed.count(True) == 0:
                # No new request
                self.direction = 0
                continue

            if self.direction:
                self.move_lift()
                if self.buttons_pressed[self.current_pos]:  # Passenger dropped based on button request
                    self.buttons_pressed[self.current_pos] = False
                    # print(f"Passenger Dropped at floor: {self.current_pos}")

                if (self.direction == 1 and (
                        self.floor_requests[self.current_pos] == 1 or self.floor_requests[self.current_pos] == 3)):
                    self.button_request()  # it should allow only up direction button request
                    self.find_destination_on_button_requests()
                    # print(f"Passenger picked up at floor: {self.current_pos} for destination: {self.destination}")

                elif (self.direction == 2 and (
                        self.floor_requests[self.current_pos] == 2 or self.floor_requests[self.current_pos] == 3)):
                    self.button_request()  # it should allow only down direction button request
                    self.find_destination_on_button_requests()
                    # print(f"Passenger picked up at floor: {self.current_pos} for destination: {self.destination}")
                if self.destination == self.current_pos:
                    self.direction = 0

        return

    def button_request(self):
        # Creates a button request based on lift direction. If lift is at halt or has just reached
        # destination, then it generates button request based on floor request.
        # Also, resets the served floor request.

        if self.current_pos == self.destination or self.direction == 0:
            # lift has reached the destination on floor request or lift was at halt and floor request
            # was on the same floor as where lift is at halt.
            # passenger is generating button request according to floor request
            if self.current_pos == (self.NUM_FLOORS - 1):
                self.direction = 2
            elif self.current_pos == 0:
                self.direction = 1
            elif self.floor_requests[self.current_pos] == 3:
                self.direction = random.randint(1, 2)
            else:
                self.direction = self.floor_requests[self.current_pos]

        if self.direction == 1:
            if (self.current_pos + 1) == (self.NUM_FLOORS - 1):
                random_floor = self.current_pos + 1
            else:
                if self.current_pos == (self.NUM_FLOORS - 1):
                    print(f"BUG: lift at top floor and direction is up.")
                else:
                    random_floor = random.randint(self.current_pos + 1, self.NUM_FLOORS - 1)
        elif self.direction == 2:
            if (self.current_pos) == 1:
                random_floor = 0;
            else:
                if self.current_pos == 0:
                    print(f"BUG: lift at 0 floor and direction is down.")
                else:
                    random_floor = random.randint(0, self.current_pos - 1)
        else:
            print(f"BUG: direction is 0")

        if self.floor_requests[self.current_pos] > 0:
            self.buttons_pressed[random_floor] = True
            self.floor_requests[self.current_pos] -= self.direction
            print(f"button request for floor {random_floor}")
        else:
            print(f"BUG: button_request on floor with no pending floor_request")
        self.update_buttons()
        return

    def find_farthest_floor_from_current_lift_position(self):
        # Iterate through floor requests list and find out distance from cur pos at each floor number.
        # Whichever floor is farthest from current life position, set the destination to that floor.
        max_distance = -1
        destination = self.destination
        if self.direction == 0:
            start_floor = 0
            end_floor = self.NUM_FLOORS
        elif self.direction == 1:
            start_floor = self.current_pos + 1
            end_floor = self.NUM_FLOORS
        else:
            start_floor = 0
            end_floor = self.current_pos
        for index in range(start_floor, end_floor):
            if self.floor_requests[index] > 0:
                if abs(self.current_pos - index) > max_distance:
                    max_distance = abs(self.current_pos - index)
                    destination = index
        return destination

    def find_destination_on_floor_requests(self):
        # Checks for any new floor request raised. If yes, depending on direction of lift,
        # destination is revised.
        if self.floor_requests.count(0) == self.NUM_FLOORS:
            # No new floor request, so return.
            return

        # There is an active floor request.
        destination = self.find_farthest_floor_from_current_lift_position()
        if destination == self.current_pos:
            # floor request is on same floor where lift is at halt. So pick up the passenger and
            # allow to raise button request. Based on the button request, set the destination.
            self.button_request()
            self.find_destination_on_button_requests()
            # print(f"Passenger picked up at floor: {self.current_pos} for destination: {self.destination}")
        elif destination > self.current_pos:
            self.direction = 1
            self.destination = destination
        else:
            self.direction = 2
            self.destination = destination

    def move_lift(self):
        # moves the lift
        if self.current_pos == 0 or self.current_pos == self.NUM_FLOORS - 1:
            if self.current_pos == 0:
                if self.floor_requests.count(0) == self.NUM_FLOORS and self.buttons_pressed.count(True) == 0:
                    self.direction = 0
                else:
                    self.direction = 1
                    self.current_pos += 1
                    # print(f"Reversing lift direction to up. Current pos: {self.current_pos}")
            else:
                if self.floor_requests.count(0) == self.NUM_FLOORS and self.buttons_pressed.count(True) == 0:
                    self.direction = 0
                else:
                    self.direction = 2
                    self.current_pos -= 1
                    # print(f"Reversing lift direction to down. Current pos: {self.current_pos}")
        else:
            if self.direction == 1:
                self.current_pos += 1
                if self.current_pos == self.NUM_FLOORS - 1:
                    self.direction = 2
            elif self.direction == 2:
                self.current_pos -= 1
                if self.current_pos == 0:
                    self.direction = 1
        # print(f"Moving lift Direction: {self.direction} and Current_Position: {self.current_pos}, destination: {
        # self.destination}")
        button_pressed_index_list = []  # list of the floors pressed in the lift
        flr_requests = {}
        for index in range(self.NUM_FLOORS):
            if self.buttons_pressed[index] == True:
                button_pressed_index_list.append(index)
            if self.floor_requests[index] != 0:
                flr_requests[index] = self.floor_requests[index]
        # print(f"Drop off locations: {button_pressed_index_list} Floor Requests: {flr_requests}")
        self.screen.fill(self.BLACK)
        self.set_base_screen_right()
        pygame.display.update()
        time.sleep(1)


    def find_destination_on_button_requests(self):
        # Iterate through button requests list and find out distance from cur pos at each floor number.
        # Whichever is farthest floor in the direction of life movement from current lift position,
        # set the destination to that floor.
        max_distance = -1
        destination = self.current_pos
        if self.direction == 0:
            # print(f"something wrong, direction should not be 0 here.")
            start_floor = 0
            end_floor = self.NUM_FLOORS
        elif self.direction == 1:
            start_floor = self.current_pos + 1
            end_floor = self.NUM_FLOORS
        else:
            start_floor = 0
            end_floor = self.current_pos
        for index in range(start_floor, end_floor):
            if self.buttons_pressed[index] == True:
                if abs(self.current_pos - index) > max_distance:
                    max_distance = abs(self.current_pos - index)
                    destination = index
        if (self.direction == 1):
            if destination > self.destination:
                self.destination = destination
        elif (self.destination == 2):
            if destination < self.destination:
                self.destination = destination
        else:
            if destination > self.current_pos:
                self.direction = 1
                self.destination = destination
            elif destination < self.current_pos:
                self.direction = 2
                self.destination = destination
            else:
                self.direction = 0
        return

    def exit_lift_operation(self, signum, frame):
        # print(f"Received keyboard interrupt, exiting lift operation...")
        self.exit = True

    def draw_text(self, screen, msg, x, y, fsize, color):
        font = pygame.font.Font(None, fsize)
        text = font.render(msg, 1, color)
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)
        #pygame.display.update()


    def set_base_screen_right(self):

        print(self.current_pos)

        self.draw_text(self.screen, "Current Floor: ", 650, 75, 28, self.WHITE)
        self.draw_text(self.screen, f"{self.current_pos}", 760, 75, 28, self.WHITE)
        self.draw_text(self.screen, "Current Direction: ", 650, 105, 28, self.WHITE)
        self.draw_text(self.screen, f"{self.direction}", 760, 105, 28, self.WHITE)
        self.draw_text(self.screen, "Current Destination: ", 650, 135, 28, self.WHITE)
        self.draw_text(self.screen, f"{self.destination}", 760, 135, 28, self.WHITE)
        self.update_buttons()





    def update_buttons(self):

        #

        #self.screen.blit(self.bg, (0, 0))
        pygame.draw.line(self.screen, self.WHITE, (255, 25), (255, 575), 3)
        for level in range(self.NUM_FLOORS):
            y_corr = int(50 + (50 * (10 - level)))
            print()
            pygame.draw.line(self.screen, self.WHITE, (205, y_corr), (305, y_corr), 2)
            self.draw_text(self.screen, f"{level}", 185, y_corr, 26, self.WHITE)
            if self.floor_requests[level] != 0:
                if self.floor_requests[level] == 1:
                    button = "UP"
                elif self.floor_requests[level] == 2:
                    button = "DOWN"
                elif self.floor_requests[level] == 3:
                    button = "BOTH"
                self.draw_text(self.screen, f"{button}", 140, y_corr, 23, self.ORANGE)


            #if level == self.current_pos:
             #   pygame.draw.rect(self.screen, self.GREY, pygame.Rect(250, y_corr-10, 10, 20))

        pygame.draw.rect(self.screen, self.GREY, pygame.Rect(315, 50 + (50 * (10 - self.current_pos)) - 15, 20, 35))


        #

        for button in range(3):
            pygame.draw.circle(self.screen, (255, 255, 255), [585 + (button * 75), 300], 20, 0)
            pygame.draw.circle(self.screen, (255, 255, 255), [585 + (button * 75), 375], 20, 0)
            pygame.draw.circle(self.screen, (255, 255, 255), [585 + (button * 75), 450], 20, 0)


        y_ = 0
        for button_number in range(0, 7, 3):
            button = 0
            while button != 3:
                #time.sleep(3)
                #print(self.buttons_pressed)
                #print(button_number+button)
                if self.buttons_pressed[button_number+button]:
                    self.draw_text(self.screen, f"{button_number+button}", 585 + (button * 75), (300+(y_*75)), 28, self.ORANGE)
                else:
                    self.draw_text(self.screen, f"{button_number+button}", 585 + (button * 75), (300+(y_*75)), 28, self.BLACK)
                button += 1
            y_ += 1
        pygame.draw.circle(self.screen, (255, 255, 255), [585, 525], 20, 0)
        pygame.draw.circle(self.screen, (255, 255, 255), [660, 525], 20, 0)

        if self.buttons_pressed[9]:
            self.draw_text(self.screen, "9", 585, 525, 28, self.ORANGE)
        else:
            self.draw_text(self.screen, "9", 585, 525, 28, self.BLACK)
        if self.buttons_pressed[9]:
            self.draw_text(self.screen, "10", 660, 525, 28, self.BLACK)
        else:
            self.draw_text(self.screen, "10", 660, 525, 28, self.BLACK)





class Floor:
    def __init__(self, floor_number):
        self.floor_number = floor_number

    def raise_request(self):
        while not lift.exit:
            waiting_time = random.randint(10, 25)
            time.sleep(waiting_time)
            lift.scan_request(self.floor_number)
        return


lift = Lift()
signal.signal(signal.SIGINT, lift.exit_lift_operation)
threads = []
for floor_num in range(lift.NUM_FLOORS):
    threader = threading.Thread(target=Floor(floor_num).raise_request)
    threads.append(threader)
    threader.start()

lift.lift_movement()
for thr in threads:
    # print(f"Gracefully exiting thread...")
    thr.join()
# print(f"Existing lift operation...")



